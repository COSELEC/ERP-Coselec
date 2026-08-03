from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import date
from typing import List, Optional
from app.models.project.project import ProjectStatus
from app.modules.stock.schemas.partner import PartnerResponse

class ProjectBase(BaseModel):
    code: str
    nom: str
    date_debut_estimee: date
    date_fin_estimee: date
    date_fin_prevue: date
    budget_estime: Optional[float] = Field(default=0.0, ge=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None

class ProjectCreate(ProjectBase):
    status: Optional[ProjectStatus] = ProjectStatus.STUDY

class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus = ProjectStatus.STUDY
    date_debut_reelle: Optional[date] = None
    date_fin_reelle: Optional[date] = None
    budget_engage: Optional[float] = Field(default=0.0, ge=0)
    
    partners: List[PartnerResponse] = Field(default_factory=list)

    @computed_field
    def client_name(self) -> Optional[str]:
        return getattr(self, "client", None).name if getattr(self, "client", None) else None

    @computed_field
    def budget_consumed(self) -> float:
        return sum(e.amount for e in self.expenses) if getattr(self, "expenses", None) else 0.0

    @computed_field
    def employees_count(self) -> int:
        return len(set(a.employee_id for a in self.attendances)) if getattr(self, "attendances", None) else 0

    @computed_field
    def current_phase(self) -> Optional[str]:
        if getattr(self, "phases", None):
            for phase in self.phases:
                if getattr(phase, "status", None) == "In Progress": # Checking based on assumed phase status
                    return phase.nom
        return None

    model_config = ConfigDict(from_attributes=True)

class ProjectUpdate(BaseModel):
    code: Optional[str] = None
    nom: Optional[str] = None

    date_debut_estimee: Optional[date] = None
    date_fin_estimee: Optional[date] = None
    date_fin_prevue: Optional[date] = None

    status: Optional[ProjectStatus] = None

    date_debut_reelle: Optional[date] = None
    date_fin_reelle: Optional[date] = None

    budget_engage: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
