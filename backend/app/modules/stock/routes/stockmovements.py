from fastapi import (
    APIRouter,
    Depends,
    Query
)

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.stock.models.stockmovement import StockMovement
from app.modules.users.models.user import User

from app.modules.stock.schemas.stockmovements import (
    StockMovementResponse
)

router = APIRouter(
    prefix="/stock-movements",
    tags=["Stock Movements"]
)


@router.get(
    "/",
    response_model=list[StockMovementResponse]
)
def get_movements(
    product_id: int | None = Query(None),
    warehouse_id: int | None = Query(None),
    partner_id: int | None = Query(None),
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = (
        db.query(StockMovement)
        .options(
            joinedload(StockMovement.product),
            joinedload(StockMovement.warehouse),
            joinedload(StockMovement.partner)
        )
    )

    if product_id:
        query = query.filter(
            StockMovement.product_id == product_id
        )

    if warehouse_id:
        query = query.filter(
            StockMovement.warehouse_id == warehouse_id
        )

    if partner_id:
        query = query.filter(
            StockMovement.partner_id == partner_id
        )

    return (
        query
        .order_by(
            StockMovement.created_at.desc()
        )
        .all()
    )
