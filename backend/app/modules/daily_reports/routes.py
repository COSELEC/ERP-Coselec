import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User
from app.models.project.daily_report import WeeklyReport, DailyReport, ReportStatus

router = APIRouter(prefix="/reports", tags=["Reports"])

def check_create_permission(current_user: User):
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" in role_names or "DIRECTION" in role_names or "PROJECT_MANAGER" in role_names or "CHEF_EQUIPE" in role_names:
        return True
    raise HTTPException(status_code=403, detail="Non autorisé. Seulement chefs d'équipe et chefs de projet.")

def save_files(files: List[UploadFile]):
    urls = []
    for file in files:
        if file.filename:
            ext = file.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join("uploads", filename)
            with open(filepath, "wb") as f:
                f.write(file.file.read())
            urls.append(f"/uploads/{filename}")
    return urls

# ---- WEEKLY REPORTS ----

@router.post("/weekly")
def submit_weekly_report(
    project_id: int = Form(...),
    report_date: str = Form(...),
    hours_worked: float = Form(...),
    tasks_completed: str = Form(...),
    progress_percentage: Optional[int] = Form(None),
    issues_encountered: Optional[str] = Form(None),
    plan_next_week: Optional[str] = Form(None),
    photos: List[UploadFile] = File([]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_create_permission(current_user)
    user = db.query(User).filter(User.email == current_user.email).first()
    
    ref_date = date.fromisoformat(report_date)
    week_start = ref_date - timedelta(days=ref_date.weekday())
    week_end = week_start + timedelta(days=4)

    existing = db.query(WeeklyReport).filter_by(user_id=user.id, project_id=project_id, week_start=week_start).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un rapport hebdomadaire existe déjà pour cette semaine.")

    photos_urls = save_files(photos)

    report = WeeklyReport(
        user_id=user.id,
        project_id=project_id,
        report_date=ref_date,
        week_start=week_start,
        week_end=week_end,
        hours_worked=hours_worked,
        progress_percentage=progress_percentage,
        tasks_completed=tasks_completed,
        issues_encountered=issues_encountered,
        plan_next_week=plan_next_week,
        photos_urls=photos_urls,
        status=ReportStatus.SUBMITTED
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/weekly")
def list_weekly_reports(
    project_id: int = None,
    week_start: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(WeeklyReport)
    
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        user = db.query(User).filter(User.email == current_user.email).first()
        from app.models.project.project import Project
        managed_projects = [p.id for p in db.query(Project).filter(Project.manager_id == user.id).all()]
        query = query.filter((WeeklyReport.user_id == user.id) | (WeeklyReport.project_id.in_(managed_projects)))

    if project_id: query = query.filter(WeeklyReport.project_id == project_id)
    if week_start: query = query.filter(WeeklyReport.week_start == week_start)
    return query.order_by(WeeklyReport.week_start.desc()).all()

@router.patch("/weekly/{report_id}/status")
def update_weekly_report_status(report_id: int, status: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report: raise HTTPException(status_code=404)
    report.status = status
    db.commit()
    return report

# ---- DAILY REPORTS ----

@router.post("/daily")
def submit_daily_report(
    project_id: int = Form(...),
    report_date: str = Form(...),
    hours_worked: float = Form(...),
    tasks_completed: str = Form(...),
    progress_percentage: Optional[int] = Form(None),
    issues_encountered: Optional[str] = Form(None),
    plan_next_day: Optional[str] = Form(None),
    photos: List[UploadFile] = File([]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_create_permission(current_user)
    user = db.query(User).filter(User.email == current_user.email).first()
    
    ref_date = date.fromisoformat(report_date)

    existing = db.query(DailyReport).filter_by(user_id=user.id, project_id=project_id, report_date=ref_date).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un rapport journalier existe déjà pour ce jour.")

    photos_urls = save_files(photos)

    report = DailyReport(
        user_id=user.id,
        project_id=project_id,
        report_date=ref_date,
        hours_worked=hours_worked,
        progress_percentage=progress_percentage,
        tasks_completed=tasks_completed,
        issues_encountered=issues_encountered,
        plan_next_day=plan_next_day,
        photos_urls=photos_urls,
        status=ReportStatus.SUBMITTED
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/daily")
def list_daily_reports(
    project_id: int = None,
    report_date: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(DailyReport)
    
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        user = db.query(User).filter(User.email == current_user.email).first()
        from app.models.project.project import Project
        managed_projects = [p.id for p in db.query(Project).filter(Project.manager_id == user.id).all()]
        query = query.filter((DailyReport.user_id == user.id) | (DailyReport.project_id.in_(managed_projects)))

    if project_id: query = query.filter(DailyReport.project_id == project_id)
    if report_date: query = query.filter(DailyReport.report_date == report_date)
    return query.order_by(DailyReport.report_date.desc()).all()

@router.patch("/daily/{report_id}/status")
def update_daily_report_status(report_id: int, status: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report: raise HTTPException(status_code=404)
    report.status = status
    db.commit()
    return report
