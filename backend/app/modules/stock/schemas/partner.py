from pydantic import BaseModel, ConfigDict
from typing import Optional


class PartnerBase(BaseModel):
    code: str
    name: str


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None


class PartnerResponse(PartnerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
