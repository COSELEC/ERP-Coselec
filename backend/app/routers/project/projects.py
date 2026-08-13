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

    if not project_data.date_fin_prevue:
        project_data.date_fin_prevue = project_data.date_fin_estimee

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
 

@router.get("/import-template")
def download_import_template():
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Styles
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#b4c6e7', 'border': 1, 'text_wrap': True})
        yellow_header = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#ffff00', 'border': 1})
        bold_format = workbook.add_format({'bold': True, 'border': 1})
        border_format = workbook.add_format({'border': 1})
        light_blue = workbook.add_format({'bg_color': '#d9e1f2', 'border': 1, 'align': 'center'})
        blue_fill = workbook.add_format({'bg_color': '#4472c4', 'border': 1})
        red_fill = workbook.add_format({'bg_color': '#ff0000', 'border': 1})
        
        # Sheet 1: Planning
        worksheet_plan = workbook.add_worksheet('Planning')
        worksheet_plan.set_column('A:A', 5)
        worksheet_plan.set_column('B:B', 40)
        worksheet_plan.set_column('C:V', 8)
        
        # Header Rows
        worksheet_plan.merge_range('A1:V1', 'MODÈLE D\'IMPORTATION DE PROJET (NE MODIFIEZ PAS LA STRUCTURE DES COLONNES, AJOUTEZ DES LIGNES EN DESSOUS)', header_format)
        
        worksheet_plan.write('A2', 'N°', header_format)
        worksheet_plan.write('B2', 'DESIGNATION', header_format)
        
        for m in range(5):
            start_col = 2 + m*4
            worksheet_plan.merge_range(1, start_col, 1, start_col+3, f'Mois {m+1}', header_format)
            for w in range(4):
                worksheet_plan.write(2, start_col + w, f'Sem {m*4+w+1}', light_blue)
                
        # Some sample data
        worksheet_plan.write('B4', 'ETUDES', bold_format)
        worksheet_plan.write('A5', '1', border_format)
        worksheet_plan.write('B5', 'Formalités Administratives', border_format)
        worksheet_plan.write('C5', '', red_fill)
        worksheet_plan.write('D5', '', red_fill)
        
        worksheet_plan.write('B7', 'APPROVISIONNEMENT', bold_format)
        worksheet_plan.write('A8', '2', border_format)
        worksheet_plan.write('B8', 'Câbles MT et BT', border_format)
        worksheet_plan.write('E8', '', blue_fill)
        worksheet_plan.write('F8', '', blue_fill)
        worksheet_plan.write('G8', '', blue_fill)
        
        # Sheet 2: Budgets
        worksheet_budgets = workbook.add_worksheet('Budgets Prestataires')
        worksheet_budgets.set_column('A:C', 25)
        worksheet_budgets.write('A1', 'PRESTATAIRE', header_format)
        worksheet_budgets.write('B1', 'TYPE BUDGET', header_format)
        worksheet_budgets.write('C1', 'MONTANT ALLOUÉ', header_format)
        
        worksheet_budgets.write('A2', 'SENELEC', border_format)
        worksheet_budgets.write('B2', 'Matériel', border_format)
        worksheet_budgets.write('C2', 50000000, border_format)
        
    output.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="Modele_Import_Projet.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
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
def import_project_excel(
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
        summary = service.import_excel(file)
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

@router.get("/{project_id}/export-gantt")
def export_project_gantt(
    project_id: int, 
    db: Session = Depends(get_db),
    user_permissions = Depends(check_permission("projects.read"))
):
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse
    from datetime import datetime, timedelta
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
        
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.start_date).all()
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).order_by(ProjectMilestone.due_date).all()
    
    if not tasks and not milestones:
        raise HTTPException(status_code=400, detail="Aucune tâche ou jalon à exporter")
        
    # Calculate timeline
    min_date = project.date_debut_estimee or datetime.utcnow().date()
    if tasks:
        task_starts = [t.start_date for t in tasks if t.start_date]
        if task_starts:
            min_date = min(min_date, min(task_starts))
            
    max_date = min_date + timedelta(days=30)
    if tasks:
        task_ends = [t.due_date for t in tasks if t.due_date]
        if task_ends:
            max_date = max(max_date, max(task_ends))
    if milestones:
        ms_ends = [m.due_date for m in milestones if m.due_date]
        if ms_ends:
            max_date = max(max_date, max(ms_ends))
            
    total_days = (max_date - min_date).days
    total_weeks = max(8, (total_days // 7) + 2)
    total_months = max(2, (total_weeks // 4) + 1)
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#b4c6e7', 'border': 1, 'text_wrap': True})
        yellow_header = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#ffff00', 'border': 1})
        bold_format = workbook.add_format({'bold': True, 'border': 1})
        border_format = workbook.add_format({'border': 1})
        light_blue = workbook.add_format({'bg_color': '#d9e1f2', 'border': 1, 'align': 'center'})
        blue_fill = workbook.add_format({'bg_color': '#4472c4', 'border': 1})
        red_fill = workbook.add_format({'bg_color': '#ff0000', 'border': 1})
        
        worksheet_plan = workbook.add_worksheet('Planning')
        worksheet_plan.set_column('A:A', 5)
        worksheet_plan.set_column('B:B', 40)
        worksheet_plan.set_column(2, 2 + total_weeks - 1, 8)
        
        # Row 0: Project name
        worksheet_plan.merge_range(0, 2, 0, 2 + total_weeks - 1, project.nom or "Projet", bold_format)
        # Row 1: Code + dates
        worksheet_plan.merge_range('A2:B2', project.code or "CODE", header_format)
        for w in range(total_weeks):
            d = min_date + timedelta(days=w*7)
            fmt = yellow_header if w == 0 else header_format
            worksheet_plan.write(1, 2 + w, d.strftime("%d/%m/%Y"), fmt)
            worksheet_plan.write(2, 2 + w, f"S{d.isocalendar()[1]}", bold_format)
            
        worksheet_plan.write(3, 0, 'N°', header_format)
        worksheet_plan.write(3, 1, 'DESIGNATION', header_format)
        
        for m in range(total_months):
            start_col = 2 + m*4
            end_col = min(start_col + 3, 2 + total_weeks - 1)
            if start_col <= end_col:
                if start_col == end_col:
                    worksheet_plan.write(3, start_col, f'Mois {m+1}', header_format)
                else:
                    worksheet_plan.merge_range(3, start_col, 3, end_col, f'Mois {m+1}', header_format)
                    
        worksheet_plan.write(4, 0, '', header_format)
        worksheet_plan.write(4, 1, '', header_format)
        for w in range(total_weeks):
            worksheet_plan.write(4, 2 + w, f'Sem {w+1}', light_blue)
            
        row_idx = 5
        task_num = 1
        
        def write_task(t, num, idx):
            worksheet_plan.write(idx, 0, num, border_format)
            worksheet_plan.write(idx, 1, t.title, border_format)
            
            s_date = t.start_date if t.start_date else min_date
            e_date = t.due_date if t.due_date else s_date
            
            start_offset = (s_date - min_date).days // 7
            start_offset = max(0, min(start_offset, total_weeks - 1))
            
            end_offset = (e_date - min_date).days // 7
            end_offset = max(0, min(end_offset, total_weeks - 1))
            if start_offset > end_offset:
                end_offset = start_offset
                
            for w in range(total_weeks):
                fmt = border_format
                if start_offset <= w <= end_offset:
                    fmt = red_fill if "administratif" in str(t.title).lower() else blue_fill
                worksheet_plan.write(idx, 2 + w, "", fmt)
        
        for ms in milestones:
            worksheet_plan.write(row_idx, 1, ms.title.upper(), bold_format)
            for c in range(2, 2 + total_weeks):
                worksheet_plan.write(row_idx, c, "", border_format)
            worksheet_plan.write(row_idx, 0, "", border_format)
            row_idx += 1
            
            ms_tasks = [t for t in tasks if t.milestone_id == ms.id]
            for t in ms_tasks:
                write_task(t, task_num, row_idx)
                row_idx += 1
                task_num += 1
                
        unparented = [t for t in tasks if not t.milestone_id]
        if unparented:
            worksheet_plan.write(row_idx, 1, "AUTRES TACHES", bold_format)
            for c in range(2, 2 + total_weeks):
                worksheet_plan.write(row_idx, c, "", border_format)
            worksheet_plan.write(row_idx, 0, "", border_format)
            row_idx += 1
            
            for t in unparented:
                write_task(t, task_num, row_idx)
                row_idx += 1
                task_num += 1
                
    output.seek(0)
    headers = {
        'Content-Disposition': f'attachment; filename="Gantt_{project.code or project.id}.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
