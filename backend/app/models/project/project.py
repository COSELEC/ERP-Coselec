from sqlalchemy import Column, Integer, String, Date, Table, Numeric, ForeignKey, Boolean, Text, Enum as SQLEnum, Float
import enum
from sqlalchemy.orm import relationship
from app.models.relations import project_partners
from app.core.database import Base

class ProjectStatus(enum.Enum):
    STUDY = "En etude"
    PLANNED = "Planifié"
    APPROVED = "Approuvé"
    ONGOING = "En cours"
    SUSPENDED = "Suspendu"
    DELAYED = "Retardé"
    BLOCKED = "Bloqué"
    VALIDATION = "En validation"
    FINISHED = "Terminé"
    CLOSED = "Clôturé"
    CANCELED = "Annulé"


class Project(Base):
    __tablename__ = "projects"

    #champs de base
    id = Column(Integer, primary_key=True, nullable=False)
    code = Column(String(10), nullable=False, unique=True)
    nom = Column(String(255), nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.STUDY, nullable=False)
    project_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    chef_projet_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    #champs de dates
    date_debut_estimee = Column(Date, nullable=False)
    date_debut_reelle = Column(Date, nullable=True)
    date_fin_estimee = Column(Date, nullable=False)
    date_fin_prevue = Column(Date, nullable=False)
    date_fin_reelle= Column(Date, nullable=True)

    #champs de coûts
    budget_estime = Column(Numeric(14, 2), default=0.0, nullable=True)
    budget_engage = Column(Numeric(14, 2), default=0.0, nullable=True)

    #géolocalisation
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String(255), nullable=True)

    #relationships
    partners = relationship(
        "Partner", 
        secondary=project_partners, 
        back_populates="projects"
    )
    client = relationship("Client")
    chef_projet = relationship("Employee")
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    budgets = relationship("ProjectBudget", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")
    assignments = relationship("ProjectAssignment", back_populates="project", cascade="all, delete-orphan")
    attendances = relationship("Attendance", overlaps="project")
