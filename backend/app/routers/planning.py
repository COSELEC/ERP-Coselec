from datetime import datetime, time, timedelta
import unicodedata
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security.auth import check_permission, get_current_user
from app.models.hr.attendance import Attendance, AttendanceStatus
from app.models.notification import NotificationType
from app.models.project.assignment import ProjectAssignment
from app.modules.users.models.user import User
from app.schemas.hr.hr import AttendanceUpdate
from app.services.availability import is_employee_on_leave
from app.services.email import send_ticket_email
from app.services.notification import create_notification

router = APIRouter(prefix="/hr", tags=["HR Planning"])


def _normalize_status_token(value: str) -> str:
    stripped = (
        unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    )
    return stripped.strip().replace("-", "_").replace(" ", "_").upper()


def _parse_attendance_status(value: str) -> AttendanceStatus:
    token = _normalize_status_token(value)

    for status in AttendanceStatus:
        if token == _normalize_status_token(status.name) or token == _normalize_status_token(status.value):
            return status

    if token == "CONGE":
        return AttendanceStatus.CONGE
    if token == "CHANTIER":
        return AttendanceStatus.CHANTIER
    if token == "SITE":
        return AttendanceStatus.SITE
    if token == "TELETRAVAIL":
        return AttendanceStatus.TELETRAVAIL

    raise ValueError(f"Unsupported status: {value}")


def _status_to_frontend_token(value: str) -> str:
    try:
        return _parse_attendance_status(value).name
    except ValueError:
        return "SITE"


@router.get("/schedule-matrix")
@router.get("/schedule-matrix/", include_in_schema=False)
def get_schedule_matrix(
    start_date: str = Query(..., description="Date de début au format YYYY-MM-DD"),
    days_count: int = Query(7, description="Nombre de jours à afficher dans la matrice"),
    department_id: Optional[int] = Query(None, description="Filtrer par ID de département"),
    _: None = Depends(check_permission("hr.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD."
        )

    date_range = [start + timedelta(days=i) for i in range(days_count)]
    if not date_range:
        return []

    users_query = db.query(User).options(joinedload(User.department)).filter(User.is_active == True)
    if department_id is not None:
        users_query = users_query.filter(User.department_id == department_id)
    users = users_query.all()

    end_date = date_range[-1]
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end_date, time.max)

    # Fetch explicit attendance overrides for date range
    overrides = (
        db.query(Attendance)
        .filter(Attendance.date >= start_dt, Attendance.date <= end_dt)
        .all()
    )
    override_map = {(o.user_id, o.date.date()): o.status for o in overrides}

    # Fetch project assignments active in date range
    assignments = (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.start_date <= end_date,
            (ProjectAssignment.end_date == None) | (ProjectAssignment.end_date >= start),
        )
        .all()
    )
    assigned_user_dates = set()
    for a in assignments:
        a_start = max(a.start_date, start)
        a_end = min(a.end_date, end_date) if a.end_date else end_date
        cur = a_start
        while cur <= a_end:
            assigned_user_dates.add((a.user_id, cur))
            cur += timedelta(days=1)

    response_matrix = []

    for emp in users:
        schedule_days = []
        emp_name = (
            f"{emp.first_name or ''} {emp.last_name or ''}".strip()
            or emp.name
            or f"Employé #{emp.id}"
        )
        emp_role = emp.position or "Collaborateur"
        dept_id = emp.department_id or 1

        for current_date in date_range:
            # 1. Weekends default to NONE (Off-duty)
            if current_date.weekday() >= 5:
                current_status = "NONE"
            else:
                db_lookup_key = (emp.id, current_date)
                # 2. Check explicit override
                if db_lookup_key in override_map:
                    current_status = _status_to_frontend_token(override_map[db_lookup_key])
                # 3. Check approved/pending leave requests
                elif is_employee_on_leave(db, emp.id, current_date):
                    current_status = "CONGE"
                # 4. Check project assignment on chantier
                elif db_lookup_key in assigned_user_dates:
                    current_status = "CHANTIER"
                # 5. Default to SITE (office)
                else:
                    current_status = "SITE"

            schedule_days.append(current_status)

        response_matrix.append(
            {
                "id": emp.id,
                "name": emp_name,
                "role": emp_role,
                "department_id": dept_id,
                "department_name": emp.department.name if emp.department else None,
                "schedule": schedule_days,
            }
        )

    return response_matrix


@router.post("/assignment")
@router.post("/assignment/", include_in_schema=False)
def update_attendance_slot(
    payload: AttendanceUpdate,
    background_tasks: BackgroundTasks,
    _: None = Depends(check_permission("hr.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user_id = payload.user_id or payload.employee_id
    emp_exists = db.query(User).filter(User.id == target_user_id).first()
    if not emp_exists:
        raise HTTPException(status_code=404, detail="Collaborateur introuvable.")

    try:
        status_enum = _parse_attendance_status(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Statut invalide. Choisissez parmi: CHANTIER, SITE, CONGE, TELETRAVAIL",
        )

    slot_date_start = datetime.combine(payload.date, time.min)
    slot_date_end = datetime.combine(payload.date, time.max)

    existing_record = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == target_user_id,
            Attendance.date >= slot_date_start,
            Attendance.date <= slot_date_end,
        )
        .first()
    )

    if existing_record:
        existing_record.status = status_enum.name
        existing_record.notes = payload.notes
        if payload.project_id is not None:
            existing_record.project_id = payload.project_id
    else:
        new_record = Attendance(
            user_id=target_user_id,
            date=datetime.combine(payload.date, time.min),
            status=status_enum.name,
            notes=payload.notes,
            project_id=payload.project_id,
        )
        db.add(new_record)

    db.commit()

    if emp_exists.email:
        date_formatee = payload.date.strftime("%d/%m/%Y")
        sujet_mail = f"Mise à jour de votre planning : {date_formatee}"
        corps_mail = f"""
        <p>Bonjour {emp_exists.first_name or ''},</p>
        <p>Le service RH a mis à jour votre planning pour la journée du <strong>{date_formatee}</strong>.</p>
        <p>Votre nouveau statut est : <span style="color: #2563eb; font-weight: bold;">{status_enum.value}</span>.</p>
        """
        if payload.notes:
            corps_mail += f"<p><em>Note du service RH : {payload.notes}</em></p>"
        corps_mail += "<p>Cordialement,<br>L'équipe Coselec</p>"

        try:
            background_tasks.add_task(
                send_ticket_email,
                email_to=emp_exists.email,
                subject=sujet_mail,
                body=corps_mail,
            )
        except Exception:
            pass

    employee_label = (
        f"{emp_exists.first_name or ''} {emp_exists.last_name or ''}".strip()
        or emp_exists.name
        or f"Employé #{emp_exists.id}"
    )

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Planning mis à jour pour {employee_label} le {payload.date}",
        type=NotificationType.INFO,
        reference_id=target_user_id,
    )

    return {"message": "Planning mis à jour avec succès"}
