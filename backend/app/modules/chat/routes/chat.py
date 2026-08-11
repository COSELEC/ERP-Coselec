import os
import uuid
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi.responses import RedirectResponse
from app.services.storage import upload_file_to_minio, get_file_url_from_minio

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    UploadFile,
    File,
    HTTPException,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.database import SessionLocal, get_db
from app.core.security.auth import get_current_user, get_current_user_ws
from app.modules.chat.models.chat import Message, ChatRoom
from app.modules.users.models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatConnectionManager:
    def __init__(self):
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_rooms:
            if websocket in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(websocket)
            if len(self.active_rooms[room_id]) == 0:
                del self.active_rooms[room_id]

    async def broadcast_json(self, data: dict, room_id: str):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                await connection.send_json(data)


manager = ChatConnectionManager()

class CreateRoomRequest(BaseModel):
    user_id: int

class CreateGroupRequest(BaseModel):
    name: str
    user_ids: List[int]

@router.get("/users")
def get_chat_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch available users to chat with."""
    users = db.query(User).filter(User.id != current_user.id, User.is_active == True).all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]

@router.get("/rooms")
def get_user_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all chat rooms for the current user."""
    rooms = db.query(ChatRoom).filter(ChatRoom.members.any(id=current_user.id)).all()
    result = []
    for room in rooms:
        other_members = [m for m in room.members if m.id != current_user.id]
        room_name = room.name
        if not room.is_group and not room_name:
            room_name = getattr(other_members[0], "name", "Utilisateur") if other_members else "Utilisateur inconnu"
        
        last_message = db.query(Message).filter(Message.room_id == room.id).order_by(Message.created_at.desc()).first()
        
        result.append({
            "id": room.id,
            "name": room_name,
            "is_group": room.is_group,
            "last_message": last_message.text if last_message else None,
            "last_message_time": last_message.created_at.isoformat() if last_message and last_message.created_at else room.created_at.isoformat() if room.created_at else None,
            "other_user_id": other_members[0].id if not room.is_group and other_members else None
        })
    result.sort(key=lambda x: x["last_message_time"] or "", reverse=True)
    return result

@router.post("/rooms")
def create_or_get_room(
    req: CreateRoomRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or get an existing 1-on-1 chat room with a user."""
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        
    existing_rooms = db.query(ChatRoom).filter(
        ChatRoom.is_group == False,
        ChatRoom.members.any(id=current_user.id),
        ChatRoom.members.any(id=target_user.id)
    ).all()
    
    if existing_rooms:
        return {"id": str(existing_rooms[0].id)}
        
    new_room = ChatRoom(is_group=False)
    new_room.members.extend([current_user, target_user])
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return {"id": str(new_room.id)}

@router.post("/groups")
def create_group_room(
    req: CreateGroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new group chat room."""
    users = db.query(User).filter(User.id.in_(req.user_ids)).all()
    if not users:
        raise HTTPException(status_code=400, detail="Aucun utilisateur valide pour le groupe")

    new_room = ChatRoom(name=req.name, is_group=True)
    new_room.members.append(current_user)
    for u in users:
        if u.id != current_user.id:
            new_room.members.append(u)
            
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return {"id": str(new_room.id)}


@router.get("/{room_id}/messages")
def get_room_messages(
    room_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches the latest messages for a specific chat room.
    """
    messages = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": msg.id,
            "room_id": msg.room_id,
            "sender_id": msg.sender_id,
            "sender_name": getattr(msg.sender, "name", f"User #{msg.sender_id}"),
            "text": msg.text,
            "file_url": msg.file_url,
            "file_name": msg.file_name,
            "file_type": msg.file_type,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]


@router.post("/{room_id}/upload")
async def upload_chat_file(
    room_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Uploads a file/image to the server and returns the local URL path.
    """
    ext = Path(file.filename).suffix if file.filename else ""
    unique_filename = f"chat/{room_id}/chat_{uuid.uuid4().hex}{ext}"
    
    try:
        storage_path = upload_file_to_minio(file, unique_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

    return {
        "file_url": f"/chat/files/{storage_path}",
        "file_name": file.filename,
        "file_type": file.content_type,
    }


@router.get("/files/{file_path:path}")
def download_chat_file(file_path: str):
    """
    Redirects to the presigned URL for the given chat file in R2/MinIO.
    """
    try:
        url = get_file_url_from_minio(file_path)
        return RedirectResponse(url)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Erreur lors de la récupération du fichier")


@router.websocket("/ws/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint that authenticates JWT via query param or cookie, listens for
    incoming messages, saves them to PostgreSQL, and broadcasts JSON payloads.
    """
    db: Session = SessionLocal()

    try:
        actual_token = token or websocket.cookies.get("access_token")
        current_user = await get_current_user_ws(actual_token, db)
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(websocket, room_id)

        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            new_message = Message(
                room_id=int(room_id),
                sender_id=current_user.id,
                text=data.get("text"),
                file_url=data.get("file_url"),
                file_name=data.get("file_name"),
                file_type=data.get("file_type"),
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            payload = {
                "id": new_message.id,
                "room_id": new_message.room_id,
                "sender_id": current_user.id,
                "sender_name": getattr(current_user, "name", f"User #{current_user.id}"),
                "text": new_message.text,
                "file_url": new_message.file_url,
                "file_name": new_message.file_name,
                "file_type": new_message.file_type,
                "created_at": new_message.created_at.isoformat(),
            }
            await manager.broadcast_json(payload, room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"WebSocket execution error: {e}")
        manager.disconnect(websocket, room_id)
    finally:
        db.close()