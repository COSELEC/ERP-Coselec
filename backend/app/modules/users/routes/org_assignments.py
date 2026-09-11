"""
Route pour les affectations d'organigramme : /org-assignments
Stocke les correspondances {position_key: str, employee_id: int} en base.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db, Base
from app.core.security.auth import get_current_user, check_permission
from app.modules.users.models.user import User


# ─── Modèle SQLAlchemy ────────────────────────────────────────────────────────

class OrgAssignment(Base):
    __tablename__ = "org_assignments"
    id = Column(Integer, primary_key=True, index=True)
    position_key = Column(String, unique=True, nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


# ─── Schémas Pydantic ─────────────────────────────────────────────────────────

class OrgAssignmentIn(BaseModel):
    position_key: str
    employee_id: Optional[int] = None


class OrgAssignmentOut(BaseModel):
    id: int
    position_key: str
    employee_id: Optional[int] = None

    class Config:
        from_attributes = True


# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/org-assignments", tags=["Org Chart"])


@router.get("", response_model=list[OrgAssignmentOut])
def get_org_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne toutes les affectations de l'organigramme."""
    return db.query(OrgAssignment).all()


@router.post("", response_model=OrgAssignmentOut)
def set_org_assignment(
    data: OrgAssignmentIn,
    _: None = Depends(check_permission("employees.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée ou met à jour l'affectation pour un poste donné."""
    existing = db.query(OrgAssignment).filter(
        OrgAssignment.position_key == data.position_key
    ).first()

    if existing:
        existing.employee_id = data.employee_id
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_asg = OrgAssignment(
            position_key=data.position_key,
            employee_id=data.employee_id
        )
        db.add(new_asg)
        db.commit()
        db.refresh(new_asg)
        return new_asg
