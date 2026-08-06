from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional

class AssignmentBase(BaseModel):
    role: str
    allocation: float = Field(..., ge=0, le=100)
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None

class AssignmentCreate(AssignmentBase):
    user_id: int

class AssignmentUpdate(BaseModel):
    role: Optional[str] = None
    allocation: Optional[float] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

class AssignmentUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    position: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class AssignmentProject(BaseModel):
    id: int
    nom: str
    code: str
    model_config = ConfigDict(from_attributes=True)

class AssignmentResponse(AssignmentBase):
    id: int
    project_id: int
    user_id: int
    user: Optional[AssignmentUser] = None
    project: Optional[AssignmentProject] = None
    current_status: str

    model_config = ConfigDict(from_attributes=True)
