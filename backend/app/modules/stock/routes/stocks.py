from fastapi import (
    APIRouter,
    Depends,
    Query
)

from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.stock.models.stock import Stock
from app.modules.users.models.user import User

from app.modules.stock.schemas.stock import StockResponse


router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"]
)


@router.get("", response_model=list[StockResponse])
def get_stocks(
    product_id: int | None = Query(None),
    warehouse_id: int | None = Query(None),
    partner_id: int | None = Query(None),
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Stock)

    if product_id:
        query = query.filter(
            Stock.product_id == product_id
        )

    if warehouse_id:
        query = query.filter(
            Stock.warehouse_id == warehouse_id
        )

    if partner_id:
        query = query.filter(
            Stock.partner_id == partner_id
        )

    return query.all()

@router.get("/general", response_model=list[StockResponse])
def get_general_stocks(
    product_id: int | None = Query(None),
    warehouse_id: int | None = Query(None),
    partner_id: int | None = Query(None),
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Stock).filter(Stock.stock_type == "GENERAL")

    if product_id:
        query = query.filter(Stock.product_id == product_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)
    if partner_id:
        query = query.filter(Stock.partner_id == partner_id)

    return query.all()


@router.get("/projects/{project_id}", response_model=list[StockResponse])
def get_project_stocks(
    project_id: int,
    product_id: int | None = Query(None),
    warehouse_id: int | None = Query(None),
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Stock).filter(Stock.stock_type == "PROJECT", Stock.project_id == project_id)

    if product_id:
        query = query.filter(Stock.product_id == product_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)

    return query.all()
