from pydantic import BaseModel, model_validator
from datetime import date, datetime
from typing import Optional
from app.models.hr.document import DocumentCategory
class AttendanceUpdate(BaseModel):
    user_id: int
    date: date
    status: str
    notes: Optional[str] = None
    project_id: Optional[int] = None

    class Config:
        from_attributes = True

class TimeclockResponse(BaseModel):
    id: int
    user_id: int
    date: datetime
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class TimeclockHistoryItem(BaseModel):
    id: int
    user_id: int
    user_name: str
    date: datetime
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True

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
