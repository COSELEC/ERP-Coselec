from pydantic import BaseModel
from typing import List, Optional

class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_codes: List[str] = []

class RoleUpdate(RoleBase):
    permission_codes: Optional[List[str]] = None

class RoleResponse(RoleBase):
    id: int
    permissions: List[PermissionResponse]

    class Config:
        from_attributes = True
