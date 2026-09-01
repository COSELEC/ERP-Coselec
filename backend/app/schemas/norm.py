from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class NormCategoryBase(BaseModel):
    name: str

class NormCategoryCreate(NormCategoryBase):
    pass

class NormCategoryResponse(NormCategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class NormVersionBase(BaseModel):
    version_number: int
    file_url: str
    is_active: bool

class NormVersionResponse(NormVersionBase):
    id: int
    norm_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NormBase(BaseModel):
    code: str
    title: str
    category_id: Optional[int] = None

class NormCreate(NormBase):
    pass

class NormResponse(NormBase):
    id: int
    category: Optional[NormCategoryResponse] = None
    versions: List[NormVersionResponse] = []
    model_config = ConfigDict(from_attributes=True)
