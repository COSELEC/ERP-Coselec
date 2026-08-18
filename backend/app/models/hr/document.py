import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.project.task import Task

class DocumentCategory(str, enum.Enum):
    IDENTITY = "Identité"
    SOCIAL = "Social/Familial"
    CONTRACT = "Contrat"


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(DocumentCategory), nullable=False)
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False) 
    mime_type = Column(String)
    
    numero = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True) 
    is_verified = Column(Boolean, default=False) 

    user = relationship("User", back_populates="documents")

class TaskDocument(Base):
    __tablename__ = "task_documents"
    id = Column(Integer, primary_key=True, nullable=False)
    task_id = Column(Integer,ForeignKey("tasks.id"), nullable=False)
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)

    uploaded_at = Column(DateTime, default = datetime.now)

    task = relationship("Task", back_populates="documents")
