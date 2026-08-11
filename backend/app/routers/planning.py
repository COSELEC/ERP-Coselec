from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time
import unicodedata
from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db
from app.modules.users.models.user import User
from app.models.hr.attendance import Attendance, AttendanceStatus
from app.models.notification import NotificationType
from app.modules.users.models.user import User
from app.schemas.hr.hr import AttendanceUpdate
from app.services.notification import create_notification
from app.services.email import send_ticket_email

router = APIRouter(prefix="/hr", tags=["HR Planning"])


def _normalize_status_token(value: str) -> str:
    stripped = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return stripped.strip().replace("-", "_").replace(" ", "_").upper()


def _parse_attendance_status(value: str) -> AttendanceStatus:
    token = _normalize_status_token(value)

    for status in AttendanceStatus:
        if token == _normalize_status_token(status.name) or token == _normalize_status_token(status.value):
            return status

    if token == "CONGE":
        return AttendanceStatus.CONGE

    raise ValueError(f"Unsupported status: {value}")


def _status_to_frontend_token(value: str) -> str:
    try:
        return _parse_attendance_status(value).name
    except ValueError:
        return "SITE"

@router.get("/schedule-matrix")
@router.get("/schedule-matrix", include_in_schema=False)
def get_schedule_matrix(
    start_date: str = Query(..., description="Date de début au format YYYY-MM-DD"),
    days_count: int = Query(7, description="Nombre de jours à afficher dans la matrice"),
    _: None = Depends(check_permission("hr.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD.")
    
    date_range = [start + timedelta(days=i) for i in range(days_count)]
    users = db.query(User).all()
    
    end_date = date_range[-1]
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end_date, time.max)
    overrides = db.query(Attendance).filter(
        Attendance.date >= start_dt,
        Attendance.date <= end_dt
    ).all()
    
    override_map = {(o.user_id, o.date.date()): o.status for o in overrides}
    
    response_matrix = []
    
    for emp in users:
        schedule_days = []
        for current_date in date_range:
            
            if current_date.weekday() >= 5: 
                current_status = "NONE"
            
            else:
                db_lookup_key = (emp.id, current_date)
                if db_lookup_key in override_map:
                    current_status = _status_to_frontend_token(override_map[db_lookup_key])
                else:
                    current_status = "SITE"

            schedule_days.append(current_status)
            
        response_matrix.append({
            "id": emp.id,
            "name": f"{emp.first_name} {emp.last_name}" if hasattr(emp, 'first_name') else emp.name,
            "role": emp.role if hasattr(emp, 'role') else "Technicien",
            "department_id": emp.department_id if hasattr(emp, 'department_id') else 1,
            "schedule": schedule_days
        })
        
    return response_matrix


@router.post("/assignment")
@router.post("/assignment", include_in_schema=False)
def update_attendance_slot(
    payload: AttendanceUpdate,
    background_tasks: BackgroundTasks, 
    _: None = Depends(check_permission("hr.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp_exists = db.query(User).filter(User.id == payload.user_id).first()
    if not emp_exists:
        raise HTTPException(status_code=404, detail="Collaborateur introuvable.")
        
    try:
        status_enum = _parse_attendance_status(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Statut invalide. Choisissez parmi: CHANTIER, SITE, CONGE, TELETRAVAIL")

    existing_record = db.query(Attendance).filter(
        Attendance.user_id == payload.user_id,
        func.date(Attendance.date) == payload.date
    ).first()
    
    if existing_record:
        if status_enum == AttendanceStatus.SITE:
            db.delete(existing_record)
        else:
            existing_record.status = status_enum.value
            existing_record.notes = payload.notes
            existing_record.project_id = payload.project_id
    else:
        if status_enum != AttendanceStatus.SITE:
            new_record = Attendance(
                user_id=payload.user_id,
                date=datetime.combine(payload.date, time.min),
                status=status_enum.value,
                notes=payload.notes,
                project_id=payload.project_id
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

        background_tasks.add_task(
            send_ticket_email,
            email_to=emp_exists.email,
            subject=sujet_mail,
            body=corps_mail
        )

    employee_label = (
        f"{emp_exists.first_name or ''} {emp_exists.last_name or ''}".strip()
        or f"Employe #{emp_exists.id}"
    )

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Planning mis a jour pour {employee_label} le {payload.date}",
        type=NotificationType.INFO,
        reference_id=payload.user_id
    )

    return {"message": "Planning mis à jour avec succès"}
