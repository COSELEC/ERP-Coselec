from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from app.models.hr.attendance import Attendance, AttendanceStatus

def process_approved_leave(db: Session, requester_id: int, start_date, end_date):
    """
    Crée des entrées d'Attendance pour chaque jour ouvré du congé.
    Ignore les week-ends (samedi, dimanche).
    """
    current_date = start_date
    while current_date <= end_date:
        # 5 = Saturday, 6 = Sunday
        if current_date.weekday() not in [5, 6]:
            # Create or update attendance
            # Check if attendance already exists
            existing = db.query(Attendance).filter(
                Attendance.user_id == requester_id,
                Attendance.date == datetime.combine(current_date, datetime.min.time())
            ).first()
            
            if existing:
                existing.status = AttendanceStatus.CONGE.value
            else:
                new_attendance = Attendance(
                    user_id=requester_id,
                    date=datetime.combine(current_date, datetime.min.time()),
                    status=AttendanceStatus.CONGE.value,
                    notes="Congé approuvé via le système de demandes"
                )
                db.add(new_attendance)
        
        current_date += timedelta(days=1)
    
    db.commit()
