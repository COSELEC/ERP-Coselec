import os
from contextlib import asynccontextmanager
from alembic import command
from alembic.config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict

from app.core.database import SessionLocal
from app.core.security.middleware import SlidingSessionMiddleware
from app.modules.requests_unified.routes.requests import (
    router as generic_requests_router,
)
from app.modules.users.routes.auth import router as auth_router
from app.modules.users.routes.employees import router as employees_router
from app.modules.users.routes.users import router as users_router
from app.modules.users.services.rbac import (
    ensure_admin_role_for_email,
    ensure_rbac_setup,
)
from app.routers.bank_vouchers import router as bank_vouchers_router
from app.routers.caisse import router as caisse_router
from app.routers.contracts import router as contracts_router
from app.routers.dashboard import router as app_dashboard_router
from app.routers.departments import router as departments_router
from app.routers.documents import router as documents_router
from app.routers.notifications import router as notifications_router
from app.routers.planning import router as planning_router
from app.routers.portfolio import router as portfolio_router
from app.routers.norms import router as norms_router
from app.routers.procurement import router as procurement_router
from app.routers.project.assignments import router as assignments_router
from app.routers.project.budget import router as budgets_router
from app.routers.project.projects import router as projects_router
from app.routers.project.tasks import router as tasks_router
from app.modules.stock.routes import stock_router

from app.tasks.hr_alerts import check_document_expirations
from app.tasks.daily_reports_alerts import check_missing_daily_reports

from app.modules.chat.routes.chat import router as chat_router
from app.modules.daily_reports.routes import router as daily_reports_router

class ConnectionManager:
    def __init__(self):
        # Use a dictionary to map a specific chat_id to a list of WebSockets
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str):
        # 1. CRITICAL: You must accept the connection first
        await websocket.accept()
        
        # 2. Create the room if it doesn't exist, then add the user
        if chat_id not in self.active_rooms:
            self.active_rooms[chat_id] = []
        self.active_rooms[chat_id].append(websocket)
        
        print(f"Client connected to chat {chat_id}. Total in room: {len(self.active_rooms[chat_id])}")

    def disconnect(self, websocket: WebSocket, chat_id: str):
        # Remove the user from the specific room
        if chat_id in self.active_rooms:
            if websocket in self.active_rooms[chat_id]:
                self.active_rooms[chat_id].remove(websocket)
            
            # Clean up empty rooms to save memory
            if len(self.active_rooms[chat_id]) == 0:
                del self.active_rooms[chat_id]
                
        print(f"Client disconnected from chat {chat_id}")

    async def broadcast(self, message: str, chat_id: str):
        # Send message ONLY to users in this specific chat_id
        if chat_id in self.active_rooms:
            for connection in self.active_rooms[chat_id]:
                await connection.send_text(message)
        
manager = ConnectionManager()   

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migrations automatiques de la base de données (Alembic)
    try:
        print("Lancement des migrations Alembic...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Base de données mise à jour avec succès !")
    except Exception as e:
        print(f"Erreur lors des migrations Alembic : {e}")

    #  Initialisation des rôles et de l'admin
    db = SessionLocal()
    try:
        ensure_rbac_setup(db)
        ensure_admin_role_for_email(db, "adam@adam.com")
    finally:
        db.close()

    # Démarrage du planificateur de tâches
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_document_expirations, "cron", hour=8, minute=0)
    scheduler.add_job(check_missing_daily_reports, "cron", day_of_week="mon-fri", hour=16, minute=0)
    scheduler.start()

    yield

    # Arrêt du planificateur à l'extinction
    scheduler.shutdown()


# Inactivation des redirections strictes de slashes pour corriger les erreurs CORS/307
app = FastAPI(lifespan=lifespan, redirect_slashes=False)

class StripTrailingSlashASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path != "/" and path.endswith("/"):
                scope["path"] = path.rstrip("/")
        await self.app(scope, receive, send)

app.add_middleware(StripTrailingSlashASGIMiddleware)

# Configuration CORS
raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "https://erp-coselec-gold.vercel.app",
]
allow_origins = [
    origin.strip().rstrip("/")
    for origin in (raw_origins.split(",") if raw_origins else default_origins)
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|.*\.vercel\.app|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|192\.190\.100\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.add_middleware(SlidingSessionMiddleware)

# Enregistrement des routeurs
app.include_router(employees_router)
app.include_router(stock_router)
app.include_router(app_dashboard_router)
app.include_router(planning_router)
app.include_router(notifications_router)
app.include_router(contracts_router)
app.include_router(documents_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(budgets_router)
app.include_router(assignments_router)
app.include_router(procurement_router)
app.include_router(portfolio_router)
app.include_router(auth_router)
app.include_router(caisse_router)
app.include_router(departments_router)
app.include_router(users_router)
app.include_router(generic_requests_router)
app.include_router(bank_vouchers_router)
app.include_router(norms_router)
app.include_router(chat_router)
app.include_router(daily_reports_router)

# Gestion du dossier des uploads
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def root():
    return {"message": "Welcome to the ERP API!"}

@app.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    await manager.connect(websocket, chat_id)
    try:
        while True:
            # Wait for messages from the frontend
            data = await websocket.receive_text()
            
            # Broadcast to everyone in this specific chat room
            await manager.broadcast(f"User says: {data}", chat_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
        await manager.broadcast("A user left the chat.", chat_id)