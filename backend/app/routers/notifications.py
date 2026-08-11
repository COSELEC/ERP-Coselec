from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.security.auth import get_current_user, get_current_user_ws, check_permission
from app.core.database import get_db, SessionLocal
from app.core.websockets.manager import notifier
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

@router.websocket("/ws")
async def websocket_notifications(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time notifications.
    Authenticates the user and registers the socket.
    """
    db: Session = SessionLocal()
    try:
        actual_token = token or websocket.cookies.get("access_token")
        current_user = await get_current_user_ws(actual_token, db)
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await notifier.connect(websocket, current_user.id)

        while True:
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        notifier.disconnect(websocket, current_user.id)
    except Exception as e:
        print(f"Notification WS Error: {e}")
        notifier.disconnect(websocket, current_user.id)
    finally:
        db.close()

