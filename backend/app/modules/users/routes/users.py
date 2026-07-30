from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security.auth import require_admin_role
from app.modules.users.models.user import User
from app.modules.users.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.modules.users.services import user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_admin_role)]
)

@router.get("", response_model=UserListResponse)
def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    total, users = user_service.get_users(db, skip=skip, limit=limit, search=search, include_inactive=include_inactive)
    return UserListResponse(total=total, page=skip // limit + 1, size=limit, items=users)

@router.post("", response_model=dict)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        if not existing_user.is_active:
            # If the user was soft-deleted, we permanently delete the old record
            # to allow recreating a new user with the same email.
            db.delete(existing_user)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="L'email est déjà utilisé.")
        
    user, temp_pwd = user_service.create_user(db, user_data, current_user)
    
    return {
        "user": UserResponse.from_orm(user),
        "temporary_password": temp_pwd
    }

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    # If updating email, check for conflicts
    if user_data.email:
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="L'email est déjà utilisé.")
            
    updated_user = user_service.update_user(db, user_id, user_data, current_user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
        
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte.")
        
    success = user_service.delete_user(db, user_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    return None
