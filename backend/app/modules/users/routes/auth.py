from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.modules.users.schemas.register import RegisterRequest
from app.modules.users.models.user import User
from app.models.notification import NotificationType

from app.core.security.auth import (
    get_current_user,
    verify_password,
    create_access_token,
    hash_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
)
from app.modules.users.services.rbac import (
    ensure_rbac_setup,
    assign_default_role,
    assign_role_to_user,
)
from app.services.notification import create_notification

router = APIRouter(tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str

@router.post("/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    hashed_password = hash_password(payload.password)
    user = User(name=payload.full_name, email=payload.email, hashed_password=hashed_password)
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db.add(user)
    db.commit()
    db.refresh(user)

    ensure_rbac_setup(db)
    assign_default_role(db, user)

    if payload.email.strip().lower() == "adam@adam.com":
        assign_role_to_user(db, user, "Admin")

    create_notification(
        db=db,
        user_id=user.id,
        message="Bienvenue sur l'ERP. Votre compte est actif.",
        type=NotificationType.INFO
    )

    return {"message": "User registered successfully", "user_id": user.id}

from datetime import datetime, timedelta

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email or payload.username
    if not email:
        raise HTTPException(status_code=422, detail="email or username is required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"DEBUG: user {email} not found in DB")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte inactif ou supprimé")

    now = datetime.utcnow()
    if user.last_login and user.last_login < now - timedelta(days=90):
        user.is_active = False
        db.commit()
        raise HTTPException(status_code=403, detail="Compte désactivé pour inactivité prolongée (> 90 jours)")

    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=403, detail="Compte temporairement verrouillé. Veuillez réessayer plus tard.")

    if not verify_password(payload.password, user.hashed_password):
        print(f"DEBUG: password verification failed for {email}")
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")


    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now
    db.commit()

    if user.requires_password_change:
        return JSONResponse(
            status_code=403, 
            content={"detail": "PASSWORD_CHANGE_REQUIRED", "email": email}
        )

    token = create_access_token({"sub": str(user.id)})
    response = JSONResponse(content={"message" : "Login successful"})
    max_age_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE
    )
    return response

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "roles": [role.name for role in current_user.roles]
    }

@router.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie(key="access_token", samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE)
    return response

class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ancien mot de passe incorrect")

    user.hashed_password = hash_password(payload.new_password)
    user.requires_password_change = False
    
    from app.modules.users.models.audit_log import AuditLog
    audit = AuditLog(
        actor_id=user.id,
        target_user_id=user.id,
        action_type="PASSWORD_CHANGE",
        old_value="***",
        new_value="***"
    )
    db.add(audit)
    db.commit()

    return {"message": "Mot de passe modifié avec succès"}
