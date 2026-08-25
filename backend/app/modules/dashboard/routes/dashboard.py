from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db

from app.models.project.project import Project, ProjectStatus
from app.modules.users.models.user import User

from app.modules.stock.models.stock import Stock
from app.modules.stock.models.stockmovement import StockMovement
from app.modules.requests_unified.models.request import GenericRequest, RequestStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/kpis")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    active_projects = db.query(Project).filter(Project.status == ProjectStatus.ONGOING).count()
    total_employees = db.query(User).count()
    
    pending_statuses = [
        RequestStatus.PENDING,
        RequestStatus.PENDING_MANAGER_APPROVAL,
        RequestStatus.PENDING_FINANCE_APPROVAL
    ]
    total_pending_requests = db.query(GenericRequest).filter(GenericRequest.status.in_(pending_statuses)).count()
    
    stock_alerts = db.query(Stock).filter(Stock.quantity <= 10).count()

    return {
        "active_projects": active_projects,
        "users": total_employees,
        "pending_requests": total_pending_requests,
        "stock_alerts": stock_alerts
    }

@router.get("/recent-activity")
def get_recent_activity(db: Session = Depends(get_db)):
    activities = []
    
    latest_projects = db.query(Project).order_by(Project.id.desc()).limit(2).all()
    for p in latest_projects:
        activities.append({
            "action": f"Nouveau projet '{p.nom}' créé",
            "time": "Récemment",
            "icon": "work_outline",
            "sort_key": p.id 
        })

    latest_requests = db.query(GenericRequest).order_by(GenericRequest.created_at.desc()).limit(2).all()
    for r in latest_requests:
        activities.append({
            "action": f"Nouvelle demande {r.type.value}",
            "time": r.created_at.strftime("%d/%m/%Y") if r.created_at else "Récemment",
            "icon": "assignment",
            "sort_key": r.id + 1000 
        })

    latest_movements = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(2).all()
    for mov in latest_movements:
        activities.append({
            "action": f"Mouvement stock: {mov.quantity} {mov.product.designation if mov.product else 'produits'}",
            "time": mov.created_at.strftime("%d/%m/%Y") if mov.created_at else "Récemment",
            "icon": "inventory_2",
            "sort_key": mov.id + 2000
        })

    activities.sort(key=lambda x: x["sort_key"], reverse=True)
    
    for i, act in enumerate(activities):
        act["id"] = i + 1
        del act["sort_key"]

    return activities[:5]
