from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.modules.users.models.role import Role
from app.modules.users.models.permission import Permission
from app.modules.users.schemas.role import RoleCreate, RoleUpdate

def get_permissions(db: Session):
    return db.query(Permission).all()

def get_roles(db: Session):
    return db.query(Role).all()

def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()

def create_role(db: Session, role_data: RoleCreate):
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un rôle avec ce nom existe déjà."
        )

    permissions = db.query(Permission).filter(Permission.code.in_(role_data.permission_codes)).all()
    
    new_role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=permissions
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

def update_role(db: Session, role_id: int, role_data: RoleUpdate):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle introuvable."
        )

    if role_data.name is not None and role_data.name != role.name:
        existing = db.query(Role).filter(Role.name == role_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un rôle avec ce nom existe déjà."
            )
        role.name = role_data.name

    if role_data.description is not None:
        role.description = role_data.description

    if role_data.permission_codes is not None:
        permissions = db.query(Permission).filter(Permission.code.in_(role_data.permission_codes)).all()
        role.permissions = permissions

    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def delete_role(db: Session, role_id: int):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle introuvable."
        )
    
    if role.name == "Admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le rôle Admin ne peut pas être supprimé."
        )
    
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce rôle est assigné à des utilisateurs et ne peut être supprimé."
        )

    db.delete(role)
    db.commit()
    return True
