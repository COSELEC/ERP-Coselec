import asyncio
from typing import Dict, List
from fastapi import WebSocket

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, user_id: int, payload: dict):
        if user_id in self.active_connections:
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(payload)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")

notifier = NotificationManager()

def broadcast_notification_sync(user_id: int, payload: dict):
    """
    Safely triggers an async broadcast from synchronous code (e.g. standard db operations).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notifier.send_personal_message(user_id, payload))
    except RuntimeError:
        asyncio.run(notifier.send_personal_message(user_id, payload))

