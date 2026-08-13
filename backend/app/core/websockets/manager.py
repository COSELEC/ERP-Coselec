import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.main_loop = loop

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
    Uses the main event loop if called from a worker thread.
    """
    try:
        current_loop = asyncio.get_running_loop()
        current_loop.create_task(notifier.send_personal_message(user_id, payload))
    except RuntimeError:
        if notifier.main_loop and notifier.main_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                notifier.send_personal_message(user_id, payload),
                notifier.main_loop
            )
        else:
            try:
                asyncio.run(notifier.send_personal_message(user_id, payload))
            except Exception as e:
                print(f"Failed to dispatch broadcast notification: {e}")


