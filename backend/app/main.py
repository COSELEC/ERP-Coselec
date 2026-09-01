import os
import asyncio
import logging
from contextlib import asynccontextmanager
from alembic import command
from alembic.config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.services.storage import get_file_url_from_minio
logging.basicConfig(level=logging.INFO)

from app.core.database import SessionLocal
from app.core.security.middleware import SlidingSessionMiddleware
from app.core.websockets.manager import notifier
from app.modules.requests_unified.routes.requests import (
    router as generic_requests_router,
)
from app.modules.users.routes.auth import router as auth_router
from app.modules.users.routes.employees import router as employees_router
from app.modules.users.routes.users import router as users_router
from app.modules.users.routes.roles import router as roles_router
from app.modules.users.services.rbac import (
    ensure_admin_role_for_email,
    ensure_rbac_setup,
)
from app.modules.finance.routes.bank_vouchers import router as bank_vouchers_router
from app.modules.finance.routes.caisse import router as caisse_router
from app.modules.hr.routes.contracts import router as contracts_router
from app.modules.dashboard.routes.dashboard import router as app_dashboard_router
from app.modules.hr.routes.departments import router as departments_router
from app.modules.hr.routes.documents import router as documents_router
from app.modules.notifications.routes.notifications import router as notifications_router
from app.modules.quality.routes.norms import router as norms_router
from app.modules.procurement.routes.procurement import router as procurement_router
from app.modules.projects.routes.assignments import router as assignments_router
from app.modules.projects.routes.budget import router as budgets_router
from app.modules.projects.routes.projects import router as projects_router
from app.modules.projects.routes.tasks import router as tasks_router
from app.modules.hr.routes.planning import router as planning_router
from app.modules.stock.routes import stock_router

from app.tasks.hr_alerts import check_document_expirations
from app.tasks.daily_reports_alerts import check_missing_daily_reports
from app.tasks.stale_requests import notify_stale_requests

from app.modules.chat.routes.chat import router as chat_router
from app.modules.daily_reports.routes import router as daily_reports_router
from app.modules.quality.routes.documents import router as quality_router
from app.modules.quality.routes.kpi import router as kpi_router

from app.models.project.client import Client 
from app.models.procurement.delivery import DeliveryNote



@asynccontextmanager
async def lifespan(app: FastAPI):
    notifier.set_loop(asyncio.get_running_loop())
    try:
        print("Lancement des migrations Alembic...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Base de données mise à jour avec succès !")
    except Exception as e:
        print(f"Erreur lors des migrations Alembic : {e}")

    db = SessionLocal()
    try:
        ensure_rbac_setup(db)
        ensure_admin_role_for_email(db, "adam@adam.com")
    finally:
        db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_document_expirations, "cron", hour=8, minute=0, misfire_grace_time=60)
    scheduler.add_job(check_missing_daily_reports, "cron", day_of_week="fri", hour=16, minute=30, misfire_grace_time=60)
    scheduler.add_job(notify_stale_requests, "cron", hour=7, minute=0, misfire_grace_time=60)
    scheduler.start()

    yield

    scheduler.shutdown()


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

app.include_router(employees_router)
app.include_router(stock_router)
app.include_router(app_dashboard_router)
app.include_router(notifications_router)
app.include_router(contracts_router)
app.include_router(documents_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(budgets_router)
app.include_router(assignments_router)
app.include_router(procurement_router)
app.include_router(auth_router)
app.include_router(caisse_router)
app.include_router(departments_router)
app.include_router(planning_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(generic_requests_router)
app.include_router(bank_vouchers_router)
app.include_router(norms_router)
app.include_router(chat_router)
app.include_router(daily_reports_router)
app.include_router(quality_router)
app.include_router(kpi_router)

@app.get("/uploads/{file_path:path}")
def get_uploaded_file(file_path: str):
    url = get_file_url_from_minio(f"uploads/{file_path}")
    if not url:
        return {"error": "File not found"}
    return RedirectResponse(url)


@app.get("/")
def root():
    return {"message": "Welcome to the ERP API!"}

