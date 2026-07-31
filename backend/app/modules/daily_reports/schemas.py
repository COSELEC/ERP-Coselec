from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from app.models.project.daily_report import ReportStatus

class DailyReportCreate(BaseModel):
    project_id: int
    report_date: date = Field(default_factory=date.today)
    hours_worked: float
    progress_percentage: Optional[int] = None
    tasks_completed: str
    issues_encountered: Optional[str] = None
    plan_for_tomorrow: Optional[str] = None

class DailyReportResponse(BaseModel):
    id: int
    employee_id: int
    project_id: int
    report_date: date
    hours_worked: float
    progress_percentage: Optional[int]
    tasks_completed: str
    issues_encountered: Optional[str]
    plan_for_tomorrow: Optional[str]
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DailyReportStatusUpdate(BaseModel):
    status: ReportStatus
