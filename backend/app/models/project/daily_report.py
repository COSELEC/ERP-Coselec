import enum
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class ReportStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    report_date = Column(Date, nullable=False, default=date.today)
    hours_worked = Column(Float, nullable=False)
    progress_percentage = Column(Integer, nullable=True)
    
    tasks_completed = Column(Text, nullable=False)
    issues_encountered = Column(Text, nullable=True)
    plan_for_tomorrow = Column(Text, nullable=True)
    
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.SUBMITTED)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # A report is unique per employee, per project, per day
    __table_args__ = (
        UniqueConstraint('employee_id', 'project_id', 'report_date', name='uq_employee_project_date'),
    )

    employee = relationship("Employee")
    project = relationship("Project")
