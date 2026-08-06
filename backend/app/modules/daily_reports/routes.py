from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta

from app.core.database import get_db
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User
from app.models.project.daily_report import DailyReport, ReportStatus

from app.modules.daily_reports.schemas import (
    WeeklyReportCreate, WeeklyReportResponse, WeeklyReportStatusUpdate
)
from app.modules.daily_reports.domain.use_cases import SubmitDailyReportUseCase, _week_bounds
from app.modules.daily_reports.adapters.sqlalchemy_repo import (
    SqlAlchemyDailyReportRepository, SqlAlchemyProjectAssignmentRepository
)
from app.modules.daily_reports.domain.exceptions import DailyReportDomainException

router = APIRouter(prefix="/weekly-reports", tags=["Weekly Reports"])


@router.post("", response_model=WeeklyReportResponse)
def submit_weekly_report(
    payload: WeeklyReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'est pas un employé valide.")

    # Calcul automatique de la semaine si non fourni
    ref_date = payload.report_date or date.today()
    week_start = payload.week_start or (ref_date - timedelta(days=ref_date.weekday()))
    week_end = payload.week_end or (week_start + timedelta(days=4))

    report_repo = SqlAlchemyDailyReportRepository(db)
    assignment_repo = SqlAlchemyProjectAssignmentRepository(db)
    use_case = SubmitDailyReportUseCase(report_repo, assignment_repo)

    try:
        report = use_case.execute(
            user_id=user.id,
            project_id=payload.project_id,
            report_date=ref_date,
            week_start=week_start,
            week_end=week_end,
            hours_worked=payload.hours_worked,
            progress_percentage=payload.progress_percentage,
            tasks_completed=payload.tasks_completed,
            issues_encountered=payload.issues_encountered,
            plan_next_week=payload.plan_next_week,
        )
        db.commit()
        db.refresh(report)
        return report
    except DailyReportDomainException as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[WeeklyReportResponse])
def list_weekly_reports(
    project_id: int = None,
    week_start: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(DailyReport)

    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        user = db.query(User).filter(User.email == current_user.email).first()
        if not user:
            return []

        from app.models.project.project import Project
        managed_projects = [p.id for p in db.query(Project).filter(Project.manager_id == user.id).all()]

        # Mes rapports OU les rapports des projets que je manage
        query = query.filter(
            (DailyReport.user_id == user.id) | (DailyReport.project_id.in_(managed_projects))
        )

    if project_id:
        query = query.filter(DailyReport.project_id == project_id)
    if week_start:
        query = query.filter(DailyReport.week_start == week_start)

    return query.order_by(DailyReport.week_start.desc()).all()


@router.patch("/{report_id}/status", response_model=WeeklyReportResponse)
def update_report_status(
    report_id: int,
    payload: WeeklyReportStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Rapport introuvable.")

    role_names = [r.name.upper() for r in current_user.roles]
    is_admin = "ADMIN" in role_names or "DIRECTION" in role_names

    user = db.query(User).filter(User.email == current_user.email).first()
    is_pm = False
    if user:
        from app.models.project.project import Project
        project = db.query(Project).filter(Project.id == report.project_id).first()
        if project and project.manager_id == user.id:
            is_pm = True

    if not is_admin and not is_pm:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à valider ce rapport.")

    report.status = payload.status
    db.commit()
    db.refresh(report)
    return report
