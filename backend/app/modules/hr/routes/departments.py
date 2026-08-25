from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.users.models.department import Department
from app.core.security.auth import get_current_user

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("")
def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return [{"id": d.id, "name": d.name, "code": d.code} for d in departments]
