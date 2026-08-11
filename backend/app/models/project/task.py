from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON, Date
import enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class TaskPriority(str, enum.Enum):
    URGENT = "Urgente"
    HIGH = "Haute"
    MEDIUM = "Moyenne"
    LOW = "Basse"

class TaskStatus(str, enum.Enum):
    TODO = "A faire"
    IN_PROGRESS = "En cours"
    REVIEW = "Revue"
    DONE = "Terminée"
    ARCHIVED = "Archivée"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority),nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    due_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=True)

    author_id = Column(Integer, ForeignKey("users.id"), nullable= False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id= Column(Integer, ForeignKey("projects.id"), nullable=True)
    milestone_id = Column(Integer, ForeignKey("project_milestones.id", ondelete="SET NULL"), nullable=True)

    task_metadata = Column(JSON, nullable=True)
    weight = Column(Integer, default=1, nullable=False)

    documents = relationship("TaskDocument", back_populates="task", cascade="all, delete-orphan")
    milestone = relationship("ProjectMilestone", back_populates="tasks")
    reservations = relationship("ProjectStockReservation", back_populates="task")
    
