from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, time, timezone

from app.core.security.auth import get_current_user
from app.core.database import get_db
from app.modules.users.models.user import User
from app.models.hr.attendance import Attendance, AttendanceStatus
from app.schemas.hr.hr import TimeclockResponse, TimeclockHistoryItem

router = APIRouter(prefix="/hr/timeclock", tags=["Timeclock"])


def _get_today_record(db: Session, user_id: int) -> Attendance | None:
    """Récupère l'enregistrement d'attendance du jour pour un utilisateur."""
    today = datetime.now(timezone.utc).date()
    return db.query(Attendance).filter(
        Attendance.user_id == user_id,
        func.date(Attendance.date) == today
    ).first()


@router.get("/today", response_model=TimeclockResponse | None)
def get_today_timeclock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = _get_today_record(db, current_user.id)
    return record


@router.post("/checkin", response_model=TimeclockResponse)
def clock_in(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  
    today = now_utc.date()

    existing = _get_today_record(db, current_user.id)
    if existing:
        if existing.check_in is not None:
            raise HTTPException(
                status_code=400,
                detail="Vous avez déjà pointé votre arrivée aujourd'hui."
            )
        existing.check_in = now_utc
        db.commit()
        db.refresh(existing)
        return existing

    new_record = Attendance(
        user_id=current_user.id,
        date=datetime.combine(today, time.min),
        status=AttendanceStatus.SITE.value,
        check_in=now_utc,
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


@router.post("/checkout", response_model=TimeclockResponse)
def clock_out(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = _get_today_record(db, current_user.id)

    if not record or record.check_in is None:
        raise HTTPException(
            status_code=400,
            detail="Vous n'avez pas encore pointé votre arrivée aujourd'hui."
        )
    if record.check_out is not None:
        raise HTTPException(
            status_code=400,
            detail="Vous avez déjà pointé votre sortie aujourd'hui."
        )

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    record.check_out = now_utc
    db.commit()
    db.refresh(record)
    return record


@router.get("/history", response_model=list[TimeclockHistoryItem])
def get_timeclock_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    records = (
        db.query(Attendance)
        .filter(Attendance.date >= since)
        .filter(Attendance.check_in.isnot(None))
        .order_by(Attendance.date.desc())
        .all()
    )

    result = []
    for r in records:
        user = db.query(User).filter(User.id == r.user_id).first()
        user_name = (
            f"{user.first_name or ''} {user.last_name or ''}".strip()
            if user else f"Employé #{r.user_id}"
        )
        duration = None
        if r.check_in and r.check_out:
            duration = int((r.check_out - r.check_in).total_seconds() / 60)

        result.append(TimeclockHistoryItem(
            id=r.id,
            user_id=r.user_id,
            user_name=user_name,
            date=r.date,
            check_in=r.check_in,
            check_out=r.check_out,
            duration_minutes=duration,
        ))

    return result


@router.get("/today-all", response_model=list[TimeclockHistoryItem])
def get_all_today_timeclocks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = datetime.now(timezone.utc).date()
    records = (
        db.query(Attendance)
        .filter(func.date(Attendance.date) == today)
        .filter(Attendance.check_in.isnot(None))
        .all()
    )

    result = []
    for r in records:
        user = db.query(User).filter(User.id == r.user_id).first()
        user_name = (
            f"{user.first_name or ''} {user.last_name or ''}".strip()
            if user else f"Employé #{r.user_id}"
        )
        duration = None
        if r.check_in and r.check_out:
            duration = int((r.check_out - r.check_in).total_seconds() / 60)

        result.append(TimeclockHistoryItem(
            id=r.id,
            user_id=r.user_id,
            user_name=user_name,
            date=r.date,
            check_in=r.check_in,
            check_out=r.check_out,
            duration_minutes=duration,
        ))

    return result
