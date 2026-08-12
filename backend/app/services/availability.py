from sqlalchemy.orm import Session
from datetime import date, datetime
from app.modules.requests_unified.models.request import GenericRequest, RequestType, RequestStatus

def is_employee_on_leave(db: Session, user_id: int, start_date: date, end_date: date = None) -> bool:
    """
    Vérifie si un employé est en congé sur une période donnée.
    Si end_date n'est pas fourni, vérifie uniquement pour start_date.
    """
    if not end_date:
        end_date = start_date
        
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
        
    requests = db.query(GenericRequest).filter(
        GenericRequest.requester_id == user_id,
        GenericRequest.type == RequestType.LEAVE,
        GenericRequest.status.in_([RequestStatus.APPROVED, RequestStatus.PENDING])
    ).all()
    
    for req in requests:
        payload = req.payload or {}
        l_start_str = payload.get("start_date")
        l_end_str = payload.get("end_date")
        
        if l_start_str and l_end_str:
            try:
                l_start = datetime.strptime(l_start_str, "%Y-%m-%d").date()
                l_end = datetime.strptime(l_end_str, "%Y-%m-%d").date()
                
                if start_date <= l_end and end_date >= l_start:
                    return True
            except ValueError:
                pass

    return False
