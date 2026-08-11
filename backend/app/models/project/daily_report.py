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
    """Modèle des rapports hebdomadaires d'avancement de projet.
    La classe garde le nom DailyReport pour la compatibilité des imports existants,
    mais la table sous-jacente est désormais 'weekly_reports'.
    """
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    week_start = Column(Date, nullable=False)   
    week_end = Column(Date, nullable=False)     
    report_date = Column(Date, nullable=False, default=date.today)  

    hours_worked = Column(Float, nullable=False)
    progress_percentage = Column(Integer, nullable=True)

    tasks_completed = Column(Text, nullable=False)
    issues_encountered = Column(Text, nullable=True)
    plan_next_week = Column(Text, nullable=True)   

    status = Column(SQLEnum(ReportStatus), default=ReportStatus.SUBMITTED)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', 'week_start', name='uq_employee_project_week'),
    )

    user = relationship("User")
    project = relationship("Project")
