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
