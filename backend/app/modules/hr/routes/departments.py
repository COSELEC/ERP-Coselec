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

from pydantic import BaseModel
class DepartmentCreate(BaseModel):
    name: str
    code: str | None = None

@router.post("")
def create_department(dept: DepartmentCreate, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    existing = db.query(Department).filter(Department.name == dept.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce département existe déjà")
    new_dept = Department(name=dept.name, code=dept.code)
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return {"id": new_dept.id, "name": new_dept.name, "code": new_dept.code}

@router.put("/{dept_id}")
def update_department(dept_id: int, dept: DepartmentCreate, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    existing = db.get(Department, dept_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Département introuvable")
    existing.name = dept.name
    existing.code = dept.code
    db.commit()
    db.refresh(existing)
    return {"id": existing.id, "name": existing.name, "code": existing.code}

@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    existing = db.get(Department, dept_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Département introuvable")
    try:
        db.delete(existing)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de supprimer ce département (il est probablement utilisé).")
    return {"message": "Département supprimé"}
