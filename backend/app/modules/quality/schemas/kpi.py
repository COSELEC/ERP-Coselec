from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from app.modules.quality.models.kpi import KPIOperator

# Base Schemas
class KPIValueBase(BaseModel):
    year: int
    month: int
    value_raw: Optional[str] = None
    value_numeric: Optional[float] = None

class KPIValueCreate(KPIValueBase):
    indicator_id: int

class KPIValueResponse(KPIValueBase):
    id: int
    indicator_id: int
    
    class Config:
        from_attributes = True

class KPIYearlyTargetBase(BaseModel):
    year: int
    frequency: Optional[str] = None
    target_raw: Optional[str] = None
    target_numeric: Optional[float] = None
    target_numeric_max: Optional[float] = None
    operator: Optional[KPIOperator] = None

class KPIYearlyTargetCreate(KPIYearlyTargetBase):
    indicator_id: int

class KPIYearlyTargetResponse(KPIYearlyTargetBase):
    id: int
    indicator_id: int
    
    class Config:
        from_attributes = True

class KPIIndicatorBase(BaseModel):
    name: str

class KPIIndicatorCreate(KPIIndicatorBase):
    processus_id: int

class KPIIndicatorResponse(KPIIndicatorBase):
    id: int
    processus_id: int
    yearly_targets: List[KPIYearlyTargetResponse] = []
    values: List[KPIValueResponse] = []

    class Config:
        from_attributes = True

class KPIProcessusBase(BaseModel):
    name: str

class KPIProcessusCreate(KPIProcessusBase):
    pass

class KPIProcessusResponse(KPIProcessusBase):
    id: int
    indicators: List[KPIIndicatorResponse] = []

    class Config:
        from_attributes = True

# Import Schemas
class KPIImportPreviewResponse(BaseModel):
    sheet_names: List[str]

class KPIImportRequest(BaseModel):
    sheet_name: str
    year: int
    month_name: str # e.g. "janv-26", will be mapped to month 1

class KPIImportResponse(BaseModel):
    message: str
    imported_count: int
    updated_count: int
