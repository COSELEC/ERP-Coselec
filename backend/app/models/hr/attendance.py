from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AttendanceStatus(enum.Enum):
    CHANTIER = "Chantier"
    TELETRAVAIL = "Télétravail"
    SITE = "Site"
    CONGE = "Congé"

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    notes = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    employee = relationship("Employee", back_populates="attendances")
    project = relationship("Project")
