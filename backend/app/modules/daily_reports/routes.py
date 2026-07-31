from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User
from app.modules.users.models.employee import Employee
from app.models.project.daily_report import DailyReport, ReportStatus

from app.modules.daily_reports.schemas import DailyReportCreate, DailyReportResponse, DailyReportStatusUpdate
from app.modules.daily_reports.domain.use_cases import SubmitDailyReportUseCase
from app.modules.daily_reports.adapters.sqlalchemy_repo import SqlAlchemyDailyReportRepository, SqlAlchemyProjectAssignmentRepository
from app.modules.daily_reports.domain.exceptions import DailyReportDomainException

router = APIRouter(prefix="/daily-reports", tags=["Daily Reports"])

@router.post("", response_model=DailyReportResponse)
def submit_daily_report(
    payload: DailyReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.email == current_user.email).first()
    if not employee:
        raise HTTPException(status_code=400, detail="L'utilisateur n'est pas un employé valide.")

    report_repo = SqlAlchemyDailyReportRepository(db)
    assignment_repo = SqlAlchemyProjectAssignmentRepository(db)
    use_case = SubmitDailyReportUseCase(report_repo, assignment_repo)

    try:
        report = use_case.execute(
            employee_id=employee.id,
            project_id=payload.project_id,
            report_date=payload.report_date,
            hours_worked=payload.hours_worked,
            progress_percentage=payload.progress_percentage,
            tasks_completed=payload.tasks_completed,
            issues_encountered=payload.issues_encountered,
            plan_for_tomorrow=payload.plan_for_tomorrow
        )
        db.commit()
        db.refresh(report)
        return report
    except DailyReportDomainException as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[DailyReportResponse])
def list_daily_reports(
    project_id: int = None,
    report_date: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin, Direction, or the Employee themselves, or the PM can see this.
    # To keep it simple, we filter based on roles.
    query = db.query(DailyReport)
    
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        employee = db.query(Employee).filter(Employee.email == current_user.email).first()
        if not employee:
            return []
        
        # In a real app we'd also check if current_user is PM of project_id. 
        # For now, if no high role, can only see own reports.
        # However, we must allow PM to see their project's reports.
        from app.models.project.project import Project
        managed_projects = [p.id for p in db.query(Project).filter(Project.manager_id == employee.id).all()]
        
        # Filter: Either it's my report, OR I am the manager of the project
        query = query.filter((DailyReport.employee_id == employee.id) | (DailyReport.project_id.in_(managed_projects)))

    if project_id:
        query = query.filter(DailyReport.project_id == project_id)
    if report_date:
        query = query.filter(DailyReport.report_date == report_date)
        
    return query.order_by(DailyReport.report_date.desc()).all()

@router.patch("/{report_id}/status", response_model=DailyReportResponse)
def update_report_status(
    report_id: int,
    payload: DailyReportStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Rapport introuvable.")

    role_names = [r.name.upper() for r in current_user.roles]
    is_admin = "ADMIN" in role_names or "DIRECTION" in role_names
    
    employee = db.query(Employee).filter(Employee.email == current_user.email).first()
    is_pm = False
    if employee:
        from app.models.project.project import Project
        project = db.query(Project).filter(Project.id == report.project_id).first()
        if project and project.manager_id == employee.id:
            is_pm = True

    if not is_admin and not is_pm:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à valider ce rapport.")

    report.status = payload.status
    db.commit()
    db.refresh(report)
    return report
