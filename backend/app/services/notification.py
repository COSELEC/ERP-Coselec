from fastapi import HTTPException

from app.models.notification import Notification
from app.models.notification import NotificationType
from app.core.websockets.manager import broadcast_notification_sync

def create_notification(
    db,
    user_id: int,
    message: str,
    type: NotificationType,
    reference_id: int | None = None
):
    new_notification = Notification(
        user_id=user_id,
        message=message,
        type=type.value,
        reference_id=reference_id
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)

    payload = {
        "event_type": "NEW_NOTIFICATION",
        "data": {
            "id": new_notification.id,
            "user_id": new_notification.user_id,
            "message": new_notification.message,
            "type": new_notification.type,
            "is_read": False,
            "created_at": new_notification.created_at.isoformat() if new_notification.created_at else None,
            "reference_id": new_notification.reference_id,
        }
    }
    broadcast_notification_sync(user_id, payload)

    return new_notification
def get_notifications(
    db,
    user_id: int,
    unread_only: bool = False
):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(
        Notification.created_at.desc(),
        Notification.id.desc()
    ).all()

def mark_notification_as_read(
    db,
    notification_id: int,
    user_id: int
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.user_id == user_id)
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    notification.is_read = True
    response_payload = {
        "id": notification.id,
        "user_id": notification.user_id,
        "message": notification.message,
        "type": notification.type,
        "is_read": True,
        "created_at": notification.created_at,
        "reference_id": notification.reference_id,
    }
    db.delete(notification)
    db.commit()
    return response_payload

def get_user_notifications(
    db,
    user_id: int,
    unread_only: bool = False
):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(
        Notification.created_at.desc(),
        Notification.id.desc()
    ).all()
