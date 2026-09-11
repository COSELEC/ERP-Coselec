from pydantic import BaseModel, EmailStr
from typing import Optional, List

class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    is_employee: Optional[bool] = False
    photo_url: Optional[str] = None

class UserCreate(UserBase):
    role_name: str 
    password: Optional[str] = "password123"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_name: Optional[str] = None
    is_employee: Optional[bool] = None
    photo_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[UserResponse]
