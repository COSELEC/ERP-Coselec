from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductBase(BaseModel):
    code: str
    designation: str
    category_id: int
    reference: Optional[str] = None
    unit: Optional[str] = None
    unit_price: int = 0
    minimum_stock: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: Optional[str] = None
    designation: Optional[str] = None
    category_id: Optional[int] = None
    reference: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[int] = None
    minimum_stock: Optional[int] = None


class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
