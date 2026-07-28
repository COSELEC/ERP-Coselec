from pydantic import BaseModel, ConfigDict
from typing import Optional


class WarehouseBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None


class WarehouseResponse(WarehouseBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
