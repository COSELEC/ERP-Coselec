from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models.project.project import Project, ProjectStatus
from app.modules.stock.models.partner import Partner
from app.schemas.project.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.core.security.auth import check_permission, get_current_user
from app.modules.users.models.user import User
from app.services.pdf_generator import generate_project_report_pdf
from app.services.storage import get_file_url_from_minio
from typing import List
from sqlalchemy import or_
from app.services.project_import_service import ProjectImportService
from app.models.project.budget import ProjectBudget
from app.models.project.payment_milestone import PaymentMilestone

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_data : ProjectCreate, db: Session= Depends(get_db), user_permissions= Depends(check_permission("projects.create"))):
    existing_project = db.query(Project).filter(Project.code == project_data.code).first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un projet avec ce code existe deja"
        )

    db_project = Project(**project_data.model_dump())
    db.add(db_project)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un projet avec ce code existe deja"
        )

    db.refresh(db_project)
    return db_project

@router.get("/{project_id}/download-report")
def download_project_report(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
        
    pdf_path = generate_project_report_pdf(db_project)
    if not pdf_path:
        raise HTTPException(status_code=500, detail="Échec de la génération du PDF")
            
    url = get_file_url_from_minio(pdf_path)
    return {"pdf_url": url}

@router.post("/{project_id}/partners/{partner_id}", status_code=status.HTTP_201_CREATED)
def add_partner_to_project(
    project_id: int,
    partner_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.update"))
):

    project = db.query(Project).filter(Project.id == project_id).first()
    partner = db.query(Partner).filter(Partner.id == partner_id).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Projet non trouvé"
        )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partenaire non trouvé"
        )

    project.partners.append(partner)

    db.commit()

    return {
        "message": "Partenaire ajouté au projet"
    }


@router.get("", response_model=List[ProjectResponse], status_code=status.HTTP_200_OK)
def get_projects(
    db:Session = Depends(get_db),
    user_permissions = Depends(check_permission("projects.read")),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    query = db.query(Project)
    
    has_global_access = any(r.name in ["Admin", "Direction", "RH / Comptabilité", "Achats"] for r in current_user.roles)
    if not has_global_access:
        query = query.filter(
            or_(
                Project.chef_projet_id == current_user.id,
                Project.assignments.any(user_id=current_user.id)
            )
        )
        
    return query.options(
        joinedload(Project.client),
        joinedload(Project.expenses),
        joinedload(Project.phases)
    ).all()
 
@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def get_project(
    project_id:int,
    db:Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.read")),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    query = db.query(Project)
    
    has_global_access = any(r.name in ["Admin", "Direction", "RH / Comptabilité", "Achats"] for r in current_user.roles)
    if not has_global_access:
        query = query.filter(
            or_(
                Project.chef_projet_id == current_user.id,
                Project.assignments.any(user_id=current_user.id)
            )
        )
        
    project = query.options(
        joinedload(Project.client),
        joinedload(Project.expenses),
        joinedload(Project.phases)
    ).filter(Project.id == project_id).first()
    
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé ou accès refusé")
    return project


@router.patch("/{project_id}")
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session= Depends(get_db),
    user_permissions = Depends(check_permission("projects.update"))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    for key, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(project_id: int, db : Session= Depends(get_db), user_permissions = Depends(check_permission("projects.delete"))):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    project.status = ProjectStatus.CANCELED
    db.commit()
    return {"message" : "Project supprimé"}

@router.delete("/{project_id}/partners/{partner_id}", status_code=status.HTTP_200_OK)
def remove_partner_from_project(
    project_id: int,
    partner_id: int,
    db: Session = Depends(get_db),
    user_permissions = Depends(check_permission("projects.update"))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    partner = db.query(Partner).filter(Partner.id == partner_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvé")

    if partner not in project.partners:
        raise HTTPException(status_code=400, detail="Ce partenaire n'est pas associé à ce projet")

    project.partners.remove(partner)
    db.commit()

from app.models.project.phase import PhaseStatus
from app.models.project.task import Task, TaskStatus
from datetime import date
from collections import defaultdict
from sqlalchemy.orm import joinedload

from app.models.project.milestone import ProjectMilestone, MilestoneStatus
from app.schemas.project.milestone import MilestoneResponse

@router.get("/{project_id}/milestones", response_model=List[MilestoneResponse], status_code=status.HTTP_200_OK)
def get_project_milestones(project_id: int, db: Session = Depends(get_db)):
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).order_by(ProjectMilestone.order_index).all()
    return milestones

@router.get("/{project_id}/dashboard", status_code=status.HTTP_200_OK)
def get_project_dashboard(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).options(
        joinedload(Project.expenses),
        joinedload(Project.milestones),
        joinedload(Project.budgets),
        joinedload(Project.assignments)
    ).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    total_budget = float(sum(b.allocated_amount for b in project.budgets)) if project.budgets else float(project.budget_estime or 0.0)
    total_expenses = float(sum(e.amount for e in project.expenses)) if project.expenses else 0.0
    budget_consumed_percent = round((total_expenses / total_budget * 100), 2) if total_budget > 0 else 0.0

    total_milestones = len(project.milestones)
    completed_milestones = len([m for m in project.milestones if m.status == MilestoneStatus.ACHIEVED])
    milestones_str = f"{completed_milestones}/{total_milestones}"

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    total_weight = sum(t.weight for t in tasks)
    completed_weight = sum(t.weight for t in tasks if t.status == TaskStatus.DONE)
    progression_percent = round((completed_weight / total_weight * 100), 2) if total_weight > 0 else 0.0

    open_tasks = len([t for t in tasks if t.status != TaskStatus.DONE and t.status != TaskStatus.ARCHIVED])

    today = date.today()
    current_year = today.year
    expenses_this_year = [e for e in project.expenses if e.date_incurred and e.date_incurred.year == current_year]
    
    monthly_expenses = defaultdict(float)
    for e in expenses_this_year:
        monthly_expenses[e.date_incurred.month] += float(e.amount)

    french_months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
    chart_labels = []
    chart_data = []
    for month in range(1, 13):
        chart_labels.append(french_months[month-1])
        chart_data.append(monthly_expenses[month])

    active_assignments = [a for a in getattr(project, "assignments", []) if getattr(a, "current_status", "Active") == "Active"]
    num_assigned_employees = len(set(a.user_id for a in active_assignments))
    avg_allocation = sum(a.allocation for a in active_assignments) / len(active_assignments) if active_assignments else 0.0
    
    role_distribution = defaultdict(int)
    for a in active_assignments:
        role_distribution[a.role] += 1

    return {
        "kpis": [
            { "title": "Progression Globale", "value": f"{progression_percent}%", "color": "text-purple-600", "bg": "bg-purple-50" },
            { "title": "Jalons Terminés", "value": milestones_str, "color": "text-green-600", "bg": "bg-green-50" },
            { "title": "Budget Consommé", "value": f"{budget_consumed_percent}%", "color": "text-blue-600", "bg": "bg-blue-50" },
            { "title": "Tâches Ouvertes", "value": str(open_tasks), "color": "text-red-600", "bg": "bg-red-50" },
        ],
        "financial_chart": {
            "labels": chart_labels,
            "data": chart_data,
            "total_budget": total_budget,
            "total_expenses": total_expenses
        },
        "hr_stats": {
            "num_assigned_employees": num_assigned_employees,
            "average_allocation": round(avg_allocation, 1),
            "role_distribution": dict(role_distribution)
        }
    }

@router.post("/{project_id}/import", status_code=status.HTTP_200_OK)
async def import_project_excel(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.update"))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
        
    try:
        service = ProjectImportService(db=db, project_id=project_id)
        summary = await service.import_excel(file)
        db.commit()
        return {"message": "Importation réussie", "summary": summary}
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        import traceback
        with open("import_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.get("/{project_id}/financials")
def get_project_financials(project_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
        
    budgets = db.query(ProjectBudget).options(joinedload(ProjectBudget.partner)).filter(ProjectBudget.project_id == project_id).all()
    milestones = db.query(PaymentMilestone).options(joinedload(PaymentMilestone.partner)).filter(PaymentMilestone.project_id == project_id).all()
    
    return {
        "budgets": [{
            "id": b.id,
            "category": b.category,
            "allocated_amount": float(b.allocated_amount or 0),
            "partner_name": b.partner.name if b.partner else "Aucun"
        } for b in budgets],
        "payment_milestones": [{
            "id": m.id,
            "title": m.title,
            "amount": float(m.amount or 0),
            "due_date": m.due_date.isoformat() if m.due_date else None,
            "status": m.status,
            "partner_name": m.partner.name if m.partner else "Aucun"
        } for m in milestones]
    }
