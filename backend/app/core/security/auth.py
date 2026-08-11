from datetime import datetime, timedelta
import os
from pathlib import Path
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import WebSocket, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.core.database import get_db
from app.modules.users.models.user import User
from app.modules.users.models.role import Role
from sqlalchemy.orm import joinedload

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
security = HTTPBearer(auto_error=False)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _require_secret_key() -> str:
    if SECRET_KEY:
        return SECRET_KEY

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "SECRET_KEY is not configured. Add SECRET_KEY in backend/.env "
            "and restart the backend server."
        ),
    )


COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = (
        datetime.utcnow()
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        _require_secret_key(),
        algorithm=ALGORITHM
    )




def get_current_user(
    access_token: str | None = Cookie(default=None, alias="access_token"),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    token = access_token

    if token and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1].strip()

    if not token and credentials is not None:
        token = credentials.credentials

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            _require_secret_key(),
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).options(
        joinedload(User.roles).joinedload(Role.permissions)
    ).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user

def check_permission(required_permission: str):
    def dependency(current_user: User = Depends(get_current_user)):
        permission_checker = any(
            permission.code == required_permission
            for role in current_user.roles
            for permission in role.permissions
        )

        if not permission_checker:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Droit insuffisant pour accéder à cette ressource"
            )
            
        return current_user

    return dependency

def require_admin_role(current_user: User = Depends(get_current_user)):
    is_admin = any(role.name == "Admin" for role in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user

def require_rh_role(current_user: User = Depends(get_current_user)):
    is_rh = any(role.name in ["RH", "RH / Comptabilité"] for role in current_user.roles)
    if not is_rh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux Ressources Humaines et Comptabilité"
        )
    return current_user

async def get_current_user_ws(token: str, db: Session) -> User | None:
    """
    Validates a JWT token string (passed via WebSocket query parameter)
    and returns the authenticated User object, or None if invalid.
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
            
    except JWTError:
        return None

    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == int(user_id))
        .first()
    )

    if not user or not user.is_active:
        return None

    return user