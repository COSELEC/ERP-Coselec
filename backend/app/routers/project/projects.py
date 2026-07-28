from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models.project.project import Project, ProjectStatus
from app.modules.stock.models.partner import Partner
from app.schemas.project.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.core.security.auth import check_permission
from app.services.pdf_generator import generate_project_report_pdf
from app.services.storage import get_file_url_from_minio
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])

# POST
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
            
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


# GET
@router.get("/", response_model=List[ProjectResponse], status_code=status.HTTP_200_OK)
def get_projects(
    db:Session = Depends(get_db),
    user_permissions = Depends(check_permission("projects.read"))
):
    from sqlalchemy.orm import joinedload
    return db.query(Project).options(
        joinedload(Project.client),
        joinedload(Project.expenses),
        joinedload(Project.phases),
        joinedload(Project.attendances)
    ).all()
 
@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def get_project(
    project_id:int,
    db:Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.read")),
):
    from sqlalchemy.orm import joinedload
    project = db.query(Project).options(
        joinedload(Project.client),
        joinedload(Project.expenses),
        joinedload(Project.phases),
        joinedload(Project.attendances)
    ).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project non trouvé")
    return project


# PATCH
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


#DELETE
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

    # 1. Budget Consommé
    total_budget = float(sum(b.allocated_amount for b in project.budgets)) if project.budgets else float(project.budget_estime or 0.0)
    total_expenses = float(sum(e.amount for e in project.expenses)) if project.expenses else 0.0
    budget_consumed_percent = round((total_expenses / total_budget * 100), 2) if total_budget > 0 else 0.0

    # 2. Jalons Terminés
    total_milestones = len(project.milestones)
    completed_milestones = len([m for m in project.milestones if m.status == MilestoneStatus.ACHIEVED])
    milestones_str = f"{completed_milestones}/{total_milestones}"

    # 3. Progression Globale (Poids des tâches)
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    total_weight = sum(t.weight for t in tasks)
    completed_weight = sum(t.weight for t in tasks if t.status == TaskStatus.DONE)
    progression_percent = round((completed_weight / total_weight * 100), 2) if total_weight > 0 else 0.0

    # 4. Tâches Ouvertes
    open_tasks = len([t for t in tasks if t.status != TaskStatus.DONE and t.status != TaskStatus.ARCHIVED])

    # 5. Financial Data
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

    # 6. HR Data
    active_assignments = [a for a in getattr(project, "assignments", []) if getattr(a, "current_status", "Active") == "Active"]
    num_assigned_employees = len(set(a.employee_id for a in active_assignments))
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