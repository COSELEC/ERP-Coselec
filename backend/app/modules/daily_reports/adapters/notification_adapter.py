import logging
from app.modules.daily_reports.domain.ports import INotificationService
from app.models.notification import Notification, NotificationType
from app.core.websockets.manager import broadcast_notification_sync
from app.models.project.project import Project
from app.modules.users.models.user import User
from app.modules.users.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class WebSocketNotificationAdapter(INotificationService):
    def __init__(self, db: Session):
        self.db = db

    def notify_missing_report(self, user_id: int, project_id: int):
        # We need to find the user_id for the user, and the project name
        user = self.db.query(User).filter(User.id == user_id).first()
        project = self.db.query(Project).filter(Project.id == project_id).first()
        
        if not user or not project:
            return
            
        user = self.db.query(User).filter(User.email == user.email).first()
        if not user:
            return

        msg = f"Rappel : Vous n'avez pas encore soumis votre rapport hebdomadaire pour le projet {project.nom}."
        
        new_notification = Notification(
            user_id=user.id,
            message=msg,
            type=NotificationType.WARNING.value,
            reference_id=project.id
        )
        self.db.add(new_notification)
        self.db.flush()
        
        try:
            broadcast_notification_sync(user.id, {
                "id": new_notification.id,
                "message": msg,
                "type": "warning",
                "reference_id": project.id,
                "created_at": new_notification.created_at.isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to broadcast missing report notification: {e}")
