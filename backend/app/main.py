from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import os
from app.tasks.hr_alerts import check_document_expirations

#schemas
from app.modules.users.schemas.register import RegisterRequest

from app.core.security.middleware import SlidingSessionMiddleware
from app.modules.users.routes.auth import router as auth_router
from app.modules.users.routes.users import router as users_router
from app.modules.requests_unified.routes.requests import router as generic_requests_router

#hr routers
from app.modules.users.routes.employees import router as employees_router
from app.routers.planning import router as planning_router
from app.routers.contracts import router as contracts_router
from app.routers.documents import router as documents_router
## stock routers
from app.routers.stock.stocks import router as stocks_router
from app.routers.stock.stockoperations import router as stock_operations_router
from app.routers.stock.dashboard import router as dashboard_router
from app.routers.stock.stockmovements import router as stock_movements_router
from app.routers.stock.products import router as products_router
from app.routers.stock.warehouses import router as warehouses_router
from app.routers.stock.partners import router as partners_router
from app.routers.stock.categories import router as categories_router

#notifications router
from app.routers.notifications import router as notifications_router
#projects routers
from app.routers.project.projects import router as projects_router
from app.routers.project.tasks import router as tasks_router
from app.routers.project.budget import router as budgets_router
from app.routers.project.assignments import router as assignments_router
from app.routers.procurement import router as procurement_router
from app.routers.stock_reservations import router as stock_reservations_router
from app.routers.portfolio import router as portfolio_router

from app.core.security.auth import (
    get_current_user,
    verify_password,
    create_access_token,
    hash_password,
)
from app.core.database import Base, engine, get_db, SessionLocal

from app.modules.users.models.user import User
from app.modules.users.models.role import Role
from app.modules.users.models.employee import Employee
from app.modules.users.models.department import Department
from app.modules.users.models.permission import Permission
from app.models.stock.category import Category
from app.models.stock.partner import Partner
from app.models.stock.product import Product
from app.models.stock.stock import Stock
from app.models.stock.stockmovement import StockMovement
from app.models.stock.warehouse import Warehouse
from app.models.notification import NotificationType, Notification
from app.models.hr.contract import Contract
from app.modules.requests_unified.models.request import GenericRequest, RequestHistory
from app.models.hr.document import EmployeeDocument
from app.models.stock.reception import ReceptionControl, ReceptionControlLine

from app.models.project.project import Project
from app.models.project.client import Client
from app.models.project.phase import ProjectPhase
from app.models.project.milestone import ProjectMilestone
from app.models.project.budget import ProjectBudget
from app.models.project.expense import ProjectExpense
from app.models.hr.attendance import Attendance
from app.models.bank_voucher import BankVoucher, AnalyticalAllocation
from app.models.voucher_attachment import VoucherAttachment

from app.services.notification import create_notification
from app.modules.users.services.rbac import (
    ensure_rbac_setup,
    assign_default_role,
    ensure_admin_role_for_email,
    assign_role_to_user,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        ensure_rbac_setup(db)
        ensure_admin_role_for_email(db, "adam@adam.com")
    finally:
        db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_document_expirations, 'cron', hour=8, minute=0) 
    scheduler.start()
    yield
    scheduler.shutdown()





app = FastAPI(lifespan=lifespan)

from app.routers.caisse import router as caisse_router
from app.routers.departments import router as departments_router
from app.routers.bank_vouchers import router as bank_vouchers_router
from app.routers.norms import router as norms_router

from app.routers.dashboard import router as app_dashboard_router
from app.routers.stock.matrix import router as stock_matrix_router
from app.routers.stock.reception import router as stock_reception_router

app.include_router(employees_router)
app.include_router(stocks_router)
app.include_router(stock_operations_router)
app.include_router(app_dashboard_router)
app.include_router(dashboard_router)
app.include_router(stock_movements_router)
app.include_router(stock_matrix_router)
app.include_router(stock_reception_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(partners_router)
app.include_router(categories_router)
app.include_router(planning_router)
app.include_router(notifications_router)
app.include_router(contracts_router)
app.include_router(documents_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(budgets_router)
app.include_router(assignments_router)
app.include_router(procurement_router)
app.include_router(stock_reservations_router)
app.include_router(portfolio_router)
app.include_router(auth_router)

app.include_router(caisse_router)
app.include_router(departments_router)
app.include_router(users_router)
app.include_router(generic_requests_router)
app.include_router(bank_vouchers_router)
app.include_router(norms_router)


raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "http://192.190.100.41:5173",
    "http://192.190.100.48:5173",
    "http://192.190.100.104:5173",
    "http://localhost",
    "http://169.254.34.100:5173"
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
    expose_headers=["Content-Disposition"]
)

app.add_middleware(SlidingSessionMiddleware)


Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "Welcome to the ERP API!"}

# Trigger reload
