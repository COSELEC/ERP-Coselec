from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.modules.users.models.user import User
from app.modules.users.models.role import Role
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

async def notify_users_by_role(role_names: list[str], message: str, notification_type: NotificationType, reference_id: int | None = None):
    """
    Notifies all users holding specific roles.
    """
    db: Session = SessionLocal()
    try:
        target_users = db.query(User).join(User.roles).filter(Role.name.in_(role_names)).all()
        for user in target_users:
            db.add(Notification(
                user_id=user.id,
                message=message,
                type=notification_type.value,
                reference_id=reference_id
            ))
        db.commit()
    except Exception as e:
        logger.error(f"Error notifying roles {role_names}: {e}")
        db.rollback()
    finally:
        db.close()

async def notify_user(user_id: int, message: str, notification_type: NotificationType, reference_id: int | None = None):
    """
    Notifies a specific user.
    """
    db: Session = SessionLocal()
    try:
        db.add(Notification(
            user_id=user_id,
            message=message,
            type=notification_type.value,
            reference_id=reference_id
        ))
        db.commit()
    except Exception as e:
        logger.error(f"Error notifying user {user_id}: {e}")
        db.rollback()
    finally:
        db.close()
