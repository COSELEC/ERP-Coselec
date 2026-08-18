from pydantic import BaseModel, model_validator
from datetime import date, datetime
from typing import Optional
from app.models.hr.document import DocumentCategory
class ContractBase(BaseModel):
    user_id: int
    contract_type: str
    start_date: date
    end_date: Optional[date] = None
    is_active: Optional[bool] = True

class ContractCreate(ContractBase):
    pass

class ContractUpdate(ContractBase):
    contract_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class ContractResponse(ContractBase):
    id: int

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    category: DocumentCategory
    file_name: str
    storage_path: str
    mime_type: Optional[str] = None
    numero: Optional[str] = None
    expiry_date: Optional[date] = None
    is_verified: bool

    class Config:
        from_attributes = True


class AttendanceUpdate(BaseModel):
    employee_id: Optional[int] = None
    user_id: Optional[int] = None
    date: date
    status: str
    notes: Optional[str] = None
    project_id: Optional[int] = None

    @model_validator(mode="after")
    def check_user_id(self):
        if not self.employee_id and not self.user_id:
            raise ValueError("employee_id or user_id is required")
        if not self.user_id:
            self.user_id = self.employee_id
        if not self.employee_id:
            self.employee_id = self.user_id
        return self

