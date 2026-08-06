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
    status: Optional[str] = "CDI"
    email: EmailStr

class UserCreate(UserBase):
    role_name: str # Using role_name to easily assign a role (e.g., 'Admin', 'Employe')

class UserUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None
    email: Optional[EmailStr] = None
    role_name: Optional[str] = None

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
