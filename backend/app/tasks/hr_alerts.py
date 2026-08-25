from datetime import date, timedelta
from app.core.database import SessionLocal 
from app.models.hr.document import EmployeeDocument
from app.services.notification import create_notification 
from app.models.notification import NotificationType
from app.modules.users.models.user import User
from app.modules.users.models.role import Role

def check_document_expirations():
    db = SessionLocal() 
    try:
        today = date.today()
        target_dates = {
            180: ("dans 6 mois", "ORANGE"),
            90: ("dans 3 mois", "ORANGE"),
            30: ("dans 1 mois", "ROUGE"),
            7: ("dans 1 semaine", "ROUGE"),
            0: ("AUJOURD'HUI", "ROUGE"),
            -1: ("depuis HIER (DÉPASSÉ)", "ROUGE")
        }
        
        target_date_objects = { (today + timedelta(days=d)): info for d, info in target_dates.items() }

        expiring_docs = db.query(EmployeeDocument).filter(
            EmployeeDocument.expiry_date.in_(target_date_objects.keys())
        ).all()

        if expiring_docs:
            rh_users = db.query(User).filter(User.roles.any(Role.name.in_(["RH / Comptabilité", "Admin", "Direction"]))).all()

            for doc in expiring_docs:
                doc_date = doc.expiry_date
                if doc_date not in target_date_objects:
                    continue
                    
                time_msg, urgency = target_date_objects[doc_date]
                
                message = f"[{urgency}] Le document '{doc.category.value}' de l'employé #{doc.user_id} expire {time_msg}."
                if doc.numero:
                    message = f"[{urgency}] Le document '{doc.category.value}' (N° {doc.numero}) de l'employé #{doc.user_id} expire {time_msg}."
                
                for rh_user in rh_users:
                    create_notification(
                        db=db,
                        user_id=rh_user.id, 
                        message=message,
                        type=NotificationType.WARNING if urgency == "ORANGE" else NotificationType.ERROR,
                        reference_id=doc.id 
                    )
    finally:
        db.close() 
