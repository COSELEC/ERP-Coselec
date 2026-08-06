import secrets
import string
import json
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple

from app.modules.users.models.user import User
from app.modules.users.models.role import Role
from app.modules.users.models.audit_log import AuditLog
from app.modules.users.schemas.user import UserCreate, UserUpdate
from app.core.security.auth import hash_password
from app.modules.users.services.rbac import assign_role_to_user

def generate_temp_password(length=10) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def get_users(db: Session, skip: int = 0, limit: int = 10, search: Optional[str] = None, include_inactive: bool = False) -> Tuple[int, List[User]]:
    query = db.query(User)
    
    if not include_inactive:
        query = query.filter(User.is_active == True)
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    return total, users

def log_audit(db: Session, actor_id: int, target_user_id: int, action_type: str, old_value: Optional[str] = None, new_value: Optional[str] = None):
    audit = AuditLog(
        actor_id=actor_id,
        target_user_id=target_user_id,
        action_type=action_type,
        old_value=old_value,
        new_value=new_value
    )
    db.add(audit)

def create_user(db: Session, user_data: UserCreate, current_user: User) -> Tuple[User, str]:
    temp_password = generate_temp_password()
    hashed_pwd = hash_password(temp_password)
    
    first_name = user_data.first_name
    last_name = user_data.last_name
    name = user_data.name

    if first_name and not name:
        name = f"{first_name} {last_name or ''}".strip()
    elif name and not first_name:
        parts = name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

    new_user = User(
        name=name,
        first_name=first_name,
        last_name=last_name,
        status=user_data.status or "CDI",
        email=user_data.email,
        hashed_password=hashed_pwd,
        department_id=user_data.department_id,
        manager_id=user_data.manager_id,
        requires_password_change=True # Forcer le changement de mot de passe à la première connexion
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    if user_data.role_name:
        assign_role_to_user(db, new_user, user_data.role_name)
        
    log_audit(db, current_user.id, new_user.id, "CREATE", new_value=json.dumps({"email": user_data.email, "role": user_data.role_name}))
    db.commit()
    return new_user, temp_password

def update_user(db: Session, user_id: int, user_data: UserUpdate, current_user: User) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Anti-elevation: (We could verify here that the current_user is allowed to assign this role)
    # Right now only Admin can access this route, and Admin is the highest role.
    
    old_values = {"name": user.name, "email": user.email, "role": user.roles[0].name if user.roles else None}
    new_values = {}
    
    # Vérification des changements
    if user_data.name is not None and user.name != user_data.name:
        log_audit(db, current_user.id, user_id, "UPDATE_NAME", user.name, user_data.name)
        user.name = user_data.name
        new_values["name"] = user.name
        
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
        new_values["first_name"] = user.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
        new_values["last_name"] = user.last_name
    if user_data.status is not None:
        user.status = user_data.status
        new_values["status"] = user.status
    if user_data.department_id is not None:
        user.department_id = user_data.department_id
        new_values["department_id"] = user.department_id
    if 'manager_id' in user_data.dict(exclude_unset=True):
        user.manager_id = user_data.manager_id
        new_values["manager_id"] = user.manager_id
        
    # S'il y a un prénom et nom sans nom global
    if user.first_name and not user_data.name:
        user.name = f"{user.first_name} {user.last_name or ''}".strip()
        new_values["name"] = user.name
        
    if user_data.email is not None and user_data.email != user.email:
        user.email = user_data.email
        new_values["email"] = user.email
        
    if user_data.role_name:
        has_target_role = any(r.name == user_data.role_name for r in user.roles)
        if not has_target_role:
            target_role = db.query(Role).filter(Role.name == user_data.role_name).first()
            if target_role:
                user.roles = [target_role]
                new_values["role"] = target_role.name
                
    if new_values:
        log_audit(db, current_user.id, user.id, "UPDATE", old_value=json.dumps(old_values), new_value=json.dumps(new_values))

    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int, current_user: User) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
        
    # Soft delete instead of db.delete(user)
    user.is_active = False
    log_audit(db, current_user.id, user.id, "DELETE", old_value="active", new_value="inactive")
    db.commit()
    return True
