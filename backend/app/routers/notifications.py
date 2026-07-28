from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db
from app.modules.users.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification import (
    get_notifications,
    mark_notification_as_read
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get("", response_model=List[NotificationResponse])
def read_user_notifications(
    unread_only: bool = False,
    _: None = Depends(check_permission("notifications.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only
    )

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    _: None = Depends(check_permission("notifications.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return mark_notification_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
