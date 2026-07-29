from datetime import date, timedelta
from app.core.database import SessionLocal #
from app.models.hr.document import EmployeeDocument
from app.services.notification import create_notification #
from app.models.notification import NotificationType
from app.modules.users.models.user import User
from app.modules.users.models.role import Role

def check_document_expirations():
    db = SessionLocal() #
    try:
        today = date.today()
        warning_6m = today + timedelta(days=180) # Pastille Orange
        warning_3m = today + timedelta(days=90)  # Pastille Rouge

        expiring_docs = db.query(EmployeeDocument).filter(
            EmployeeDocument.expiry_date <= warning_6m,
            EmployeeDocument.expiry_date > today
        ).all()

        if expiring_docs:
            rh_users = db.query(User).filter(User.roles.any(Role.name == "RH")).all()

            for doc in expiring_docs:
                days_left = (doc.expiry_date - today).days
                urgency = "ROUGE" if days_left <= 90 else "ORANGE"
                
                message = f"[{urgency}] Le document {doc.category.value} de l'employé #{doc.employee_id} expire dans {days_left} jours."
                
                for rh_user in rh_users:
                    create_notification(
                        db=db,
                        user_id=rh_user.id, 
                        message=message,
                        type=NotificationType.WARNING,
                        reference_id=doc.id #
                    )
    finally:
        db.close() #
