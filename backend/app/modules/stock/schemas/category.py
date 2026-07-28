from pydantic import BaseModel, ConfigDict
from typing import Optional


class CategoryBase(BaseModel):
    code: str
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
