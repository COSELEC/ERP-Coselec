from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security.auth import check_permission, require_admin_role
from app.modules.users.schemas.role import RoleCreate, RoleUpdate, RoleResponse, PermissionResponse
from app.modules.users.services import role_service

# For managing roles, we either check for Admin or check for specific permissions.
# We'll use check_permission("roles.*") or fallback to Admin. For simplicity, we can use a combination
# or just the permissions since Admin has them all.

router = APIRouter(
    tags=["roles"],
    # For now, require 'roles.read' just to access the module, endpoints have specific checks
)

@router.get("/permissions", response_model=List[PermissionResponse], dependencies=[Depends(check_permission("roles.read"))])
def read_permissions(db: Session = Depends(get_db)):
    return role_service.get_permissions(db)

@router.get("/roles", response_model=List[RoleResponse], dependencies=[Depends(check_permission("roles.read"))])
def read_roles(db: Session = Depends(get_db)):
    return role_service.get_roles(db)

@router.get("/roles/{role_id}", response_model=RoleResponse, dependencies=[Depends(check_permission("roles.read"))])
def read_role(role_id: int, db: Session = Depends(get_db)):
    return role_service.get_role(db, role_id)

@router.post("/roles", response_model=RoleResponse, dependencies=[Depends(check_permission("roles.create"))])
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    return role_service.create_role(db, role_data)

@router.put("/roles/{role_id}", response_model=RoleResponse, dependencies=[Depends(check_permission("roles.update"))])
def update_role(role_id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    return role_service.update_role(db, role_id, role_data)

@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(check_permission("roles.delete"))])
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role_service.delete_role(db, role_id)
    return None
