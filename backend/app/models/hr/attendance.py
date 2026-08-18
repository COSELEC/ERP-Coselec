import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class AttendanceStatus(str, enum.Enum):
    CHANTIER = "Chantier"
    TELETRAVAIL = "Télétravail"
    SITE = "Site"
    CONGE = "Congé"


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    notes = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="attendances")
    project = relationship("Project")
