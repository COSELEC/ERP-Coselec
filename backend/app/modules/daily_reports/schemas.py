from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from app.models.project.daily_report import ReportStatus


def _get_week_bounds(ref_date: date):
    """Retourne (lundi, vendredi) de la semaine contenant ref_date."""
    monday = ref_date - __import__('datetime').timedelta(days=ref_date.weekday())
    friday = monday + __import__('datetime').timedelta(days=4)
    return monday, friday


class WeeklyReportCreate(BaseModel):
    project_id: int
    report_date: date = Field(default_factory=date.today)
    week_start: Optional[date] = None   # Si None, calculé depuis report_date
    week_end: Optional[date] = None
    hours_worked: float
    progress_percentage: Optional[int] = None
    tasks_completed: str
    issues_encountered: Optional[str] = None
    plan_next_week: Optional[str] = None


# Alias rétrocompatibilité
DailyReportCreate = WeeklyReportCreate


class WeeklyReportResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    week_start: date
    week_end: date
    report_date: date
    hours_worked: float
    progress_percentage: Optional[int]
    tasks_completed: str
    issues_encountered: Optional[str]
    plan_next_week: Optional[str]
    status: ReportStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alias rétrocompatibilité
DailyReportResponse = WeeklyReportResponse


class WeeklyReportStatusUpdate(BaseModel):
    status: ReportStatus


# Alias rétrocompatibilité
DailyReportStatusUpdate = WeeklyReportStatusUpdate
