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
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")
        
    pdf_path = generate_project_report_pdf(db_project)
    if not pdf_path:
        raise HTTPException(status_code=500, detail="Ã‰chec de la gÃ©nÃ©ration du PDF")
            
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
            detail="Projet non trouvÃ©"
        )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partenaire non trouvÃ©"
        )

    project.partners.append(partner)

    db.commit()

    return {
        "message": "Partenaire ajoutÃ© au projet"
    }


@router.get("", response_model=List[ProjectResponse], status_code=status.HTTP_200_OK)
def get_projects(
    db:Session = Depends(get_db),
    user_permissions = Depends(check_permission("projects.read")),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload
    query = db.query(Project)
    
    has_global_access = any(r.name in ["Admin", "Direction", "RH / ComptabilitÃ©", "Achats"] for r in current_user.roles)
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
        worksheet_plan.merge_range('A1:V1', 'MODÃˆLE D\'IMPORTATION DE PROJET (NE MODIFIEZ PAS LA STRUCTURE DES COLONNES, AJOUTEZ DES LIGNES EN DESSOUS)', header_format)
        
        worksheet_plan.write('A2', 'NÂ°', header_format)
        worksheet_plan.write('B2', 'DESIGNATION', header_format)
        
        for m in range(5):
            start_col = 2 + m*4
            worksheet_plan.merge_range(1, start_col, 1, start_col+3, f'Mois {m+1}', header_format)
            for w in range(4):
                worksheet_plan.write(2, start_col + w, f'Sem {m*4+w+1}', light_blue)
                
        # Some sample data
        worksheet_plan.write('B4', 'ETUDES', bold_format)
        worksheet_plan.write('A5', '1', border_format)
        worksheet_plan.write('B5', 'FormalitÃ©s Administratives', border_format)
        worksheet_plan.write('C5', '', red_fill)
        worksheet_plan.write('D5', '', red_fill)
        
        worksheet_plan.write('B7', 'APPROVISIONNEMENT', bold_format)
        worksheet_plan.write('A8', '2', border_format)
        worksheet_plan.write('B8', 'CÃ¢bles MT et BT', border_format)
        worksheet_plan.write('E8', '', blue_fill)
        worksheet_plan.write('F8', '', blue_fill)
        worksheet_plan.write('G8', '', blue_fill)
        
        # Sheet 2: Récap Budget
        ws_budgets = workbook.add_worksheet('Récap Budget')
        
        # Setup columns
        ws_budgets.set_column('A:A', 20)
        ws_budgets.set_column('B:E', 15)
        ws_budgets.set_column('F:L', 15)
        ws_budgets.set_column('M:M', 2) # Gap
        ws_budgets.set_column('N:N', 20)
        ws_budgets.set_column('O:P', 15)
        ws_budgets.set_column('Q:R', 10)
        ws_budgets.set_column('S:S', 15)
        
        # Title headers
        ws_budgets.merge_range('A1:L1', 'TABLEAU RECAP CONTRAT', header_format)
        ws_budgets.merge_range('N1:O1', 'ACHAT INTRANTS', header_format)
        ws_budgets.merge_range('P1:P1', 'GRUES', header_format)
        ws_budgets.merge_range('Q1:S1', 'TRANSPORT PBA', header_format)
        
        # Left table columns
        cols_left = ["PRESTATAIRES", "RÉGION", "DÉPARTEMENT", "COMMUNE", "LOCALITÉ", "MONTANT TOTAL", 
                     "Décompte N°1", "Décompte N°2", "Décompte N°3", "Décompte N°4", "Décompte N°5"]
        for i, col_name in enumerate(cols_left):
            ws_budgets.write(1, i, col_name, yellow_header)
            
        # Right table columns
        cols_right = ["PRESTATAIRES", "PT BÉTON", "LOCATION GRUE", "NBRE", "PU TTC", "TOTAL TRANSPORT"]
        for i, col_name in enumerate(cols_right):
            ws_budgets.write(1, 13 + i, col_name, light_blue)
            
        # Sample data
        ws_budgets.write(2, 0, "SENELEC", border_format)
        ws_budgets.write(2, 1, "Dakar", border_format)
        ws_budgets.write(2, 4, "Dakar Plateau", border_format)
        ws_budgets.write(2, 5, 50000000, border_format)
        ws_budgets.write(2, 6, 10000000, border_format)
        
        ws_budgets.write(2, 13, "SENELEC", border_format)
        ws_budgets.write(2, 14, 500000, border_format)
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
    
    has_global_access = any(r.name in ["Admin", "Direction", "RH / ComptabilitÃ©", "Achats"] for r in current_user.roles)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvÃ© ou accÃ¨s refusÃ©")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvÃ©")
    for key, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(project_id: int, db : Session= Depends(get_db), user_permissions = Depends(check_permission("projects.delete"))):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvÃ©")
    project.status = ProjectStatus.CANCELED
    db.commit()
    return {"message" : "Project supprimÃ©"}

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
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire non trouvÃ©")

    if partner not in project.partners:
        raise HTTPException(status_code=400, detail="Ce partenaire n'est pas associÃ© Ã  ce projet")

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
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")

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

    french_months = ["Jan", "FÃ©v", "Mar", "Avr", "Mai", "Juin", "Juil", "AoÃ»t", "Sep", "Oct", "Nov", "DÃ©c"]
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
            { "title": "Jalons TerminÃ©s", "value": milestones_str, "color": "text-green-600", "bg": "bg-green-50" },
            { "title": "Budget ConsommÃ©", "value": f"{budget_consumed_percent}%", "color": "text-blue-600", "bg": "bg-blue-50" },
            { "title": "TÃ¢ches Ouvertes", "value": str(open_tasks), "color": "text-red-600", "bg": "bg-red-50" },
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
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")
        
    try:
        service = ProjectImportService(db=db, project_id=project_id)
        summary = service.import_excel(file)
        db.commit()
        return {"message": "Importation rÃ©ussie", "summary": summary}
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
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")
        
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

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# PRIVATE HELPERS  â€“  write a single sheet into an already-open xlsxwriter
#                     workbook.  Return nothing; caller owns the workbook.
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _write_gantt_sheet(workbook, project, tasks, milestones):
    """Write the Gantt/Planning sheet into *workbook*."""
    from datetime import datetime, timedelta

    min_date = project.date_debut_estimee or project.date_debut_reelle or datetime.utcnow().date()
    if tasks:
        task_starts = [t.start_date for t in tasks if t.start_date]
        if task_starts:
            min_date = min(min_date, min(task_starts))

    max_date = project.date_fin_prevue or project.date_fin_estimee or project.date_fin_reelle or (min_date + timedelta(days=60))
    if tasks:
        task_ends = [t.due_date for t in tasks if t.due_date]
        if task_ends:
            max_date = max(max_date, max(task_ends))
    if milestones:
        ms_ends = [m.due_date for m in milestones if m.due_date]
        if ms_ends:
            max_date = max(max_date, max(ms_ends))

    if max_date <= min_date:
        max_date = min_date + timedelta(days=30)

    total_days  = max(7,  (max_date - min_date).days)
    total_weeks = max(8,  (total_days // 7) + 2)
    total_months = max(2, (total_weeks // 4) + 1)

    header_format  = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#b4c6e7', 'border': 1, 'text_wrap': True})
    yellow_header  = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#ffff00', 'border': 1})
    bold_format    = workbook.add_format({'bold': True, 'border': 1})
    border_format  = workbook.add_format({'border': 1})
    light_blue     = workbook.add_format({'bg_color': '#d9e1f2', 'border': 1, 'align': 'center'})
    blue_fill      = workbook.add_format({'bg_color': '#4472c4', 'border': 1})
    red_fill       = workbook.add_format({'bg_color': '#ff0000', 'border': 1})

    ws = workbook.add_worksheet('Planning')
    ws.set_column('A:A', 5)
    ws.set_column('B:B', 40)
    ws.set_column(2, 2 + total_weeks - 1, 8)

    ws.merge_range(0, 2, 0, 2 + total_weeks - 1, project.nom or "Projet", bold_format)
    ws.merge_range('A2:B2', project.code or "CODE", header_format)

    for w in range(total_weeks):
        d   = min_date + timedelta(days=w * 7)
        fmt = yellow_header if w == 0 else header_format
        ws.write(1, 2 + w, d.strftime("%d/%m/%Y"), fmt)
        ws.write(2, 2 + w, f"S{d.isocalendar()[1]}", bold_format)

    ws.write(3, 0, 'NÂ°', header_format)
    ws.write(3, 1, 'DESIGNATION', header_format)

    for m in range(total_months):
        start_col = 2 + m * 4
        end_col   = min(start_col + 3, 2 + total_weeks - 1)
        if start_col <= end_col:
            if start_col == end_col:
                ws.write(3, start_col, f'Mois {m+1}', header_format)
            else:
                ws.merge_range(3, start_col, 3, end_col, f'Mois {m+1}', header_format)

    ws.write(4, 0, '', header_format)
    ws.write(4, 1, '', header_format)
    for w in range(total_weeks):
        ws.write(4, 2 + w, f'Sem {w+1}', light_blue)

    row_idx  = 5
    task_num = 1

    def write_task(t, num, idx):
        ws.write(idx, 0, num, border_format)
        ws.write(idx, 1, t.title, border_format)

        s_date = t.start_date if t.start_date else min_date
        e_date = t.due_date   if t.due_date   else s_date

        start_offset = max(0, min((s_date - min_date).days // 7, total_weeks - 1))
        end_offset   = max(0, min((e_date - min_date).days // 7, total_weeks - 1))
        if start_offset > end_offset:
            end_offset = start_offset

        for w in range(total_weeks):
            fmt = border_format
            if start_offset <= w <= end_offset:
                fmt = red_fill if "administratif" in str(t.title).lower() else blue_fill
            ws.write(idx, 2 + w, "", fmt)

    for ms in milestones:
        ws.write(row_idx, 1, ms.title.upper(), bold_format)
        for c in range(2, 2 + total_weeks):
            ws.write(row_idx, c, "", border_format)
        ws.write(row_idx, 0, "", border_format)
        row_idx += 1

        for t in [t for t in tasks if t.milestone_id == ms.id]:
            write_task(t, task_num, row_idx)
            row_idx  += 1
            task_num += 1

    unparented = [t for t in tasks if not t.milestone_id]
    if unparented:
        ws.write(row_idx, 1, "AUTRES TACHES", bold_format)
        for c in range(2, 2 + total_weeks):
            ws.write(row_idx, c, "", border_format)
        ws.write(row_idx, 0, "", border_format)
        row_idx += 1
        for t in unparented:
            write_task(t, task_num, row_idx)
            row_idx  += 1
            task_num += 1

    if not milestones and not tasks:
        ws.write(row_idx, 0, 1, border_format)
        ws.write(row_idx, 1, "Aucune tÃ¢che dÃ©finie", border_format)
        for c in range(2, 2 + total_weeks):
            ws.write(row_idx, c, "", border_format)




def _write_budget_sheet(workbook, project, budgets, milestones_pay):
    """Write the Tableau Récap Contrat sheet.

    Rows: one entry per unique (partner, localite) pair derived from PaymentMilestones AND ProjectBudgets.
    Right panel: ACHAT INTRANTS / GRUES / TRANSPORT PBA from ProjectBudget categories.
    """
    import re
    from datetime import date as dt_date
    from collections import defaultdict

    _DEC_RE = re.compile(r"(?:d[ée]compte|d[ée]c\.?)\s*(?:n[°o]?\s*)?(\d+)", re.IGNORECASE)

    def _dec_index(title: str) -> int:
        m = _DEC_RE.search(title or "")
        return int(m.group(1)) if m else 0

    # ── Build row data ────────────────────────────────────────────────────────
    # Each display row = (partner_name, region, departement, commune, localite)
    row_key_data: dict = {}

    # 1. From Payment Milestones
    for m in milestones_pay:
        pname   = m.partner.name if m.partner else "Aucun"
        region  = (m.region      or "").strip()
        dept    = (m.departement or "").strip()
        commune = (m.commune     or "").strip()
        loc     = (m.localite    or "").strip()

        key = (pname, region, dept, commune, loc)
        if key not in row_key_data:
            row_key_data[key] = {"decomptes": defaultdict(float), "__total__": 0.0, "budgets": []}

        dec_i  = _dec_index(m.title)
        amount = float(m.amount or 0)
        row_key_data[key]["decomptes"][dec_i] += amount
        row_key_data[key]["__total__"]        += amount

    # 2. From Project Budgets (Right panel & global prestations)
    for b in budgets:
        pname   = b.partner.name if b.partner else "Aucun"
        region  = (getattr(b, 'region', "")      or "").strip()
        dept    = (getattr(b, 'departement', "") or "").strip()
        commune = (getattr(b, 'commune', "")     or "").strip()
        loc     = (getattr(b, 'localite', "")    or "").strip()

        key = (pname, region, dept, commune, loc)
        if key not in row_key_data:
            row_key_data[key] = {"decomptes": defaultdict(float), "__total__": 0.0, "budgets": []}
            
        row_key_data[key]["budgets"].append(b)
        if (b.category or "").strip() == "Prestation (Global)":
            row_key_data[key]["__total__"] += float(b.allocated_amount or 0)

    # Sort the rows by partner name
    rows_list = sorted(list(row_key_data.items()), key=lambda x: x[0][0])

    # Detect distinct decompte indices
    all_dec_indices = sorted({
        idx
        for _, data in rows_list
        for idx in data["decomptes"].keys()
        if isinstance(idx, int) and idx > 0
    })
    if not all_dec_indices:
        all_dec_indices = list(range(1, 6))

    NUM_DEC     = len(all_dec_indices)
    DEFAULT_PCT = {1: 20, 2: 20, 3: 30, 4: 10, 5: 20}

    # ── Category Constants ────────────────────────────────────────────────────
    BETON_CAT  = "Achat Intrants - Béton"
    CIMENT_CAT = "Achat Intrants - Ciment"
    GRUE_CAT   = "Location Grue"
    TRANSP_CAT = "Transport PBA"

    # ── Column layout ─────────────────────────────────────────────────────────
    COL_PRESTATAIRE = 0
    COL_REGION      = 1
    COL_DEPT        = 2
    COL_COMMUNE     = 3
    COL_LOCALITE    = 4
    COL_MONTANT     = 5
    COL_DEC_START   = 6
    COL_DEC_END     = COL_DEC_START + NUM_DEC - 1
    COL_GAP         = COL_DEC_END + 1
    COL_RIGHT_START = COL_GAP + 1

    R_PRESTATAIRE  = COL_RIGHT_START
    R_PT_CIMENT    = COL_RIGHT_START + 1
    R_PT_BETON     = COL_RIGHT_START + 2
    R_GRUE         = COL_RIGHT_START + 3
    R_NBRE         = COL_RIGHT_START + 4
    R_PU           = COL_RIGHT_START + 5
    R_TOTAL_TRANSP = COL_RIGHT_START + 6

    # ── Formats ───────────────────────────────────────────────────────────────
    def fmt(**kw):
        base = {"border": 1, "valign": "vcenter"}
        base.update(kw)
        return workbook.add_format(base)

    f_title        = fmt(bold=True, align="center", font_size=12, bg_color="#1F4E79", font_color="#FFFFFF")
    f_sec_hdr      = fmt(bold=True, align="center", bg_color="#1F4E79", font_color="#FFFFFF", text_wrap=True)
    f_dec_hdr      = fmt(bold=True, align="center", bg_color="#BDD7EE", font_color="#1F4E79", text_wrap=True)
    f_cell         = fmt(align="left")
    f_cell_c       = fmt(align="center")
    f_num          = fmt(align="right", num_format="#,##0")
    f_num_hl       = fmt(align="right", bold=True, bg_color="#FFFF00", num_format="#,##0")
    f_tot_label    = fmt(bold=True, align="left",  bg_color="#D6E4F0")
    f_tot_num      = fmt(bold=True, align="right", bg_color="#D6E4F0", num_format="#,##0")
    f_orange_label = fmt(bold=True, align="left",  bg_color="#F4B942", font_color="#FFFFFF")
    f_orange_num   = fmt(bold=True, align="right", bg_color="#F4B942", font_color="#FFFFFF", num_format="#,##0")
    f_green_label  = fmt(bold=True, align="left",  bg_color="#70AD47", font_color="#FFFFFF")
    f_green_num    = fmt(bold=True, align="right", bg_color="#70AD47", font_color="#FFFFFF", num_format="#,##0")
    f_gray_label   = fmt(align="left",  bg_color="#F2F2F2")
    f_gray_num     = fmt(align="right", bg_color="#F2F2F2", num_format="#,##0")
    f_rp_hdr       = fmt(bold=True, align="center", bg_color="#1F4E79", font_color="#FFFFFF", text_wrap=True)
    f_rp_sub       = fmt(bold=True, align="center", bg_color="#2E75B6", font_color="#FFFFFF", text_wrap=True)
    f_rp_cell      = fmt(align="left")
    f_rp_num       = fmt(align="right", num_format="#,##0")

    ws = workbook.add_worksheet("Tableau Récap Contrat")

    ws.set_column(COL_PRESTATAIRE, COL_PRESTATAIRE, 18)
    ws.set_column(COL_REGION,      COL_REGION,      12)
    ws.set_column(COL_DEPT,        COL_DEPT,        14)
    ws.set_column(COL_COMMUNE,     COL_COMMUNE,     14)
    ws.set_column(COL_LOCALITE,    COL_LOCALITE,    22)
    ws.set_column(COL_MONTANT,     COL_MONTANT,     16)
    for c in range(COL_DEC_START, COL_DEC_END + 1):
        ws.set_column(c, c, 14)
    ws.set_column(COL_GAP,        COL_GAP,           2)
    ws.set_column(R_PRESTATAIRE,  R_PRESTATAIRE,    16)
    ws.set_column(R_PT_CIMENT,    R_PT_CIMENT,      14)
    ws.set_column(R_PT_BETON,     R_PT_BETON,       14)
    ws.set_column(R_GRUE,         R_GRUE,           14)
    ws.set_column(R_NBRE,         R_NBRE,            8)
    ws.set_column(R_PU,           R_PU,             12)
    ws.set_column(R_TOTAL_TRANSP, R_TOTAL_TRANSP,   16)

    ws.set_row(0, 28)
    ws.set_row(1, 40)
    ws.set_row(2, 50)

    export_date = dt_date.today().strftime("%d/%m/%Y")

    # Row 0 – Titles
    ws.merge_range(0, COL_PRESTATAIRE, 0, COL_DEC_END,
                   f"TABLEAU RECAP CONTRAT {export_date}", f_title)
    ws.merge_range(0, R_PRESTATAIRE,  0, R_PT_BETON,     "ACHAT INTRANTS",  f_rp_hdr)
    ws.merge_range(0, R_GRUE,         0, R_GRUE,         "GRUES",           f_rp_hdr)
    ws.merge_range(0, R_NBRE,         0, R_TOTAL_TRANSP, "TRANSPORT PBA",   f_rp_hdr)

    # Rows 1-2 – Column headers
    ws.merge_range(1, COL_PRESTATAIRE, 2, COL_PRESTATAIRE, "PRESTATAIRES",  f_sec_hdr)
    ws.merge_range(1, COL_REGION,      2, COL_REGION,      "RÉGIONS",       f_sec_hdr)
    ws.merge_range(1, COL_DEPT,        2, COL_DEPT,        "DÉPARTEMENTS",  f_sec_hdr)
    ws.merge_range(1, COL_COMMUNE,     2, COL_COMMUNE,     "COMMUNES",      f_sec_hdr)
    ws.merge_range(1, COL_LOCALITE,    2, COL_LOCALITE,    "LOCALITÉS",     f_sec_hdr)
    ws.merge_range(1, COL_MONTANT,     2, COL_MONTANT,     "MONTANT TOTAL", f_sec_hdr)

    for i, dec_idx in enumerate(all_dec_indices):
        col = COL_DEC_START + i
        pct = DEFAULT_PCT.get(dec_idx, "")
        lbl = f"Décompte N°{dec_idx}\n{pct}%" if pct else f"Décompte N°{dec_idx}"
        ws.merge_range(1, col, 2, col, lbl, f_dec_hdr)

    ws.merge_range(1, R_PRESTATAIRE,  2, R_PRESTATAIRE,  "PRESTATAIRES",    f_rp_sub)
    ws.merge_range(1, R_PT_CIMENT,    2, R_PT_CIMENT,    "PT CIMENT",       f_rp_sub)
    ws.merge_range(1, R_PT_BETON,     2, R_PT_BETON,     "PT BÉTON",        f_rp_sub)
    ws.merge_range(1, R_GRUE,         2, R_GRUE,         "LOCATION GRUE",   f_rp_sub)
    ws.merge_range(1, R_NBRE,         2, R_NBRE,         "NBRES",           f_rp_sub)
    ws.merge_range(1, R_PU,           2, R_PU,           "PU TTC",          f_rp_sub)
    ws.merge_range(1, R_TOTAL_TRANSP, 2, R_TOTAL_TRANSP, "TOTAL TRANSPORT", f_rp_sub)

    # Data rows
    ROW_DATA_START = 3
    col_grand_total = [0.0] * (1 + NUM_DEC)
    rp_grand = {CIMENT_CAT: 0.0, BETON_CAT: 0.0, GRUE_CAT: 0.0, TRANSP_CAT: 0.0}

    for r_offset, (key, data) in enumerate(rows_list):
        pname, region, dept, commune, loc = key
        row = ROW_DATA_START + r_offset
        ws.set_row(row, 18)

        row_total = data.get("__total__", 0.0)

        ws.write(row, COL_PRESTATAIRE, pname,    f_cell)
        ws.write(row, COL_REGION,      region,   f_cell_c)
        ws.write(row, COL_DEPT,        dept,     f_cell_c)
        ws.write(row, COL_COMMUNE,     commune,  f_cell_c)
        ws.write(row, COL_LOCALITE,    loc,      f_cell)
        ws.write(row, COL_MONTANT, row_total, f_num_hl if row_total > 0 else f_num)
        col_grand_total[0] += row_total

        for i, dec_idx in enumerate(all_dec_indices):
            col     = COL_DEC_START + i
            dec_val = data["decomptes"].get(dec_idx, 0.0)
            ws.write(row, col, dec_val if dec_val else "", f_num)
            col_grand_total[1 + i] += dec_val

        # Get budgets for this specific row
        row_budgets = data["budgets"]
        
        ciment = sum(float(b.allocated_amount or 0) for b in row_budgets if (b.category or "").strip() == CIMENT_CAT)
        beton  = sum(float(b.allocated_amount or 0) for b in row_budgets if (b.category or "").strip() == BETON_CAT)
        grue   = sum(float(b.allocated_amount or 0) for b in row_budgets if (b.category or "").strip() == GRUE_CAT)
        
        # Transport PBA
        transp_b = next((b for b in row_budgets if (b.category or "").strip() == TRANSP_CAT), None)
        transp_total = float(transp_b.allocated_amount or 0) if transp_b else 0.0
        qty = float(transp_b.quantity) if transp_b and transp_b.quantity else None
        pu  = float(transp_b.unit_price) if transp_b and transp_b.unit_price else None

        ws.write(row, R_PRESTATAIRE,  pname,                      f_rp_cell)
        ws.write(row, R_PT_CIMENT,    ciment if ciment else "",   f_rp_num)
        ws.write(row, R_PT_BETON,     beton  if beton  else "",   f_rp_num)
        ws.write(row, R_GRUE,         grue   if grue   else "",   f_rp_num)
        ws.write(row, R_NBRE,         qty    if qty    else "",   f_rp_num)
        ws.write(row, R_PU,           pu     if pu     else "",   f_rp_num)
        ws.write(row, R_TOTAL_TRANSP, transp_total if transp_total else "", f_rp_num)

        rp_grand[CIMENT_CAT] += ciment
        rp_grand[BETON_CAT]  += beton
        rp_grand[GRUE_CAT]   += grue
        rp_grand[TRANSP_CAT] += transp_total

    # TOTAL ROW
    TOT_ROW = ROW_DATA_START + len(rows_list)
    ws.set_row(TOT_ROW, 22)
    ws.merge_range(TOT_ROW, COL_PRESTATAIRE, TOT_ROW, COL_LOCALITE, "TOTAL", f_tot_label)
    ws.write(TOT_ROW, COL_MONTANT, col_grand_total[0], f_tot_num)
    for i in range(NUM_DEC):
        ws.write(TOT_ROW, COL_DEC_START + i, col_grand_total[1 + i], f_tot_num)
    ws.write(TOT_ROW, R_PRESTATAIRE,  "",                                 f_tot_num)
    ws.write(TOT_ROW, R_PT_CIMENT,    rp_grand[CIMENT_CAT] or "",         f_tot_num)
    ws.write(TOT_ROW, R_PT_BETON,     rp_grand[BETON_CAT]  or "",         f_tot_num)
    ws.write(TOT_ROW, R_GRUE,         rp_grand[GRUE_CAT]   or "",         f_tot_num)
    ws.write(TOT_ROW, R_NBRE,         "",                                 f_tot_num)
    ws.write(TOT_ROW, R_PU,           "",                                 f_tot_num)
    ws.write(TOT_ROW, R_TOTAL_TRANSP, rp_grand[TRANSP_CAT] or "",         f_tot_num)

    # PRIX DE POSE
    POSE_ROW = TOT_ROW + 2
    ws.set_row(POSE_ROW, 20)
    pose_total = sum(float(b.allocated_amount or 0) for b in budgets
                     if "pose" in (b.category or "").lower())
    ws.merge_range(POSE_ROW, COL_PRESTATAIRE, POSE_ROW, COL_REGION, "PRIX DE POSE", f_orange_label)
    ws.write(POSE_ROW, COL_DEPT, pose_total if pose_total else "", f_orange_num)
    for c in range(COL_COMMUNE, COL_DEC_END + 1):
        ws.write(POSE_ROW, c, "", f_orange_num)

    debours_pose  = sum(float(b.allocated_amount or 0) for b in budgets
                        if "débours" in (b.category or "").lower() and "pose" in (b.category or "").lower())
    autres_pose   = sum(float(b.allocated_amount or 0) for b in budgets
                        if "autres"  in (b.category or "").lower() and "pose" in (b.category or "").lower())
    reliquat_pose = max(0.0, pose_total - debours_pose - autres_pose)

    for sub_offset, (label, val) in enumerate([("DÉBOURS", debours_pose), ("AUTRES", autres_pose), ("RELIQUAT", reliquat_pose)]):
        sub_row = POSE_ROW + 1 + sub_offset
        ws.set_row(sub_row, 18)
        ws.merge_range(sub_row, COL_PRESTATAIRE, sub_row, COL_REGION, label, f_gray_label)
        ws.write(sub_row, COL_DEPT, val if val else "", f_gray_num)
        for c in range(COL_COMMUNE, COL_DEC_END + 1):
            ws.write(sub_row, c, "", f_gray_num)

    # PRIX DE TRANSPORT
    TRANSP_ROW = POSE_ROW + 5
    ws.set_row(TRANSP_ROW, 20)
    transp_total = rp_grand[TRANSP_CAT] or sum(
        float(b.allocated_amount or 0) for b in budgets
        if "transport" in (b.category or "").lower()
    )
    ws.merge_range(TRANSP_ROW, COL_PRESTATAIRE, TRANSP_ROW, COL_REGION, "PRIX DE TRANSPORT", f_green_label)
    ws.write(TRANSP_ROW, COL_DEPT, transp_total if transp_total else "", f_green_num)
    for c in range(COL_COMMUNE, COL_DEC_END + 1):
        ws.write(TRANSP_ROW, c, "", f_green_num)

    debours_tr  = sum(float(b.allocated_amount or 0) for b in budgets
                      if "débours"  in (b.category or "").lower() and "transport" in (b.category or "").lower())
    autres_tr   = sum(float(b.allocated_amount or 0) for b in budgets
                      if "autres"   in (b.category or "").lower() and "transport" in (b.category or "").lower())
    reliquat_tr = max(0.0, transp_total - debours_tr - autres_tr)

    for sub_offset, (label, val) in enumerate([("DÉBOURS", debours_tr), ("AUTRES", autres_tr), ("RELIQUAT", reliquat_tr)]):
        sub_row = TRANSP_ROW + 1 + sub_offset
        ws.set_row(sub_row, 18)
        ws.merge_range(sub_row, COL_PRESTATAIRE, sub_row, COL_REGION, label, f_gray_label)
        ws.write(sub_row, COL_DEPT, val if val else "", f_gray_num)
        for c in range(COL_COMMUNE, COL_DEC_END + 1):
            ws.write(sub_row, c, "", f_gray_num)

    ws.write(TRANSP_ROW + 5, COL_DEPT, project.nom or "", f_cell)
    ws.freeze_panes(3, 1)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ENDPOINTS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/{project_id}/export-gantt")
def export_project_gantt(
    project_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.read")),
):
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")

    tasks      = db.query(Task).filter(Task.project_id == project_id).order_by(Task.start_date).all()
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).order_by(ProjectMilestone.due_date).all()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        _write_gantt_sheet(writer.book, project, tasks, milestones)

    output.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="Gantt_{project.code or project.id}.xlsx"'}
    return StreamingResponse(output, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/{project_id}/export-budget")
def export_project_budget(
    project_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.read")),
):
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")

    budgets = (
        db.query(ProjectBudget)
        .options(joinedload(ProjectBudget.partner))
        .filter(ProjectBudget.project_id == project_id)
        .all()
    )
    milestones_pay = (
        db.query(PaymentMilestone)
        .options(joinedload(PaymentMilestone.partner))
        .filter(PaymentMilestone.project_id == project_id)
        .order_by(PaymentMilestone.due_date)
        .all()
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        _write_budget_sheet(writer.book, project, budgets, milestones_pay)

    output.seek(0)
    filename = f"Budget_{project.code or project.id}.xlsx"
    resp_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(output, headers=resp_headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/{project_id}/export-combined")
def export_project_combined(
    project_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("projects.read")),
):
    """Export Gantt (Planning sheet) + Budget (Tableau RÃ©cap Contrat sheet) in a single XLSX file."""
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvÃ©")

    tasks      = db.query(Task).filter(Task.project_id == project_id).order_by(Task.start_date).all()
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).order_by(ProjectMilestone.due_date).all()
    budgets    = (
        db.query(ProjectBudget)
        .options(joinedload(ProjectBudget.partner))
        .filter(ProjectBudget.project_id == project_id)
        .all()
    )
    milestones_pay = (
        db.query(PaymentMilestone)
        .options(joinedload(PaymentMilestone.partner))
        .filter(PaymentMilestone.project_id == project_id)
        .order_by(PaymentMilestone.due_date)
        .all()
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        wb = writer.book
        _write_gantt_sheet(wb, project, tasks, milestones)
        _write_budget_sheet(wb, project, budgets, milestones_pay)

    output.seek(0)
    filename = f"Export_{project.code or project.id}.xlsx"
    resp_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(output, headers=resp_headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
