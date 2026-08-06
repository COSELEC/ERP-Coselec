from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db
from app.models.notification import NotificationType
from app.modules.stock.models.partner import Partner
from app.modules.stock.models.product import Product
from app.modules.stock.models.warehouse import Warehouse
from app.modules.users.models.user import User
from app.services.notification import create_notification

from app.modules.stock.schemas.stockoperations import (
    StockEntry,
    StockExit,
    StockTransfer,
    StockTransferToProject
)

from app.modules.stock.services.stock_service import (
    stock_entry,
    stock_exit,
    stock_transfer,
    stock_transfer_to_project
)

router = APIRouter(
    prefix="/stock",
    tags=["Stock"]
)


def _resolve_product_label(db: Session, product_id: int) -> str:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        return f"Produit #{product_id}"
    return product.designation


def _resolve_warehouse_label(db: Session, warehouse_id: int) -> str:
    warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id)
        .first()
    )
    if not warehouse:
        return f"Entrepot #{warehouse_id}"
    return warehouse.name


def _resolve_partner_label(db: Session, partner_id: int | None) -> str:
    if partner_id is None:
        return "Coselec Interne"

    partner = (
        db.query(Partner)
        .filter(Partner.id == partner_id)
        .first()
    )
    if not partner:
        return f"Partenaire #{partner_id}"
    return partner.name

@router.post("/entry")
def create_entry(
    payload: StockEntry,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = stock_entry(
        db,
        payload.product_id,
        payload.warehouse_id,
        payload.partner_id,
        payload.quantity
    )

    product_label = _resolve_product_label(db, payload.product_id)
    warehouse_label = _resolve_warehouse_label(db, payload.warehouse_id)
    partner_label = _resolve_partner_label(db, payload.partner_id)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=(
            f"Entree stock: produit {product_label}, "
            f"entrepot {warehouse_label}, "
            f"partenaire {partner_label}, "
            f"quantite {payload.quantity}"
        ),
        type=NotificationType.INFO,
        reference_id=payload.product_id
    )

    return result

@router.post("/exit")
def create_exit(
    payload: StockExit,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = stock_exit(
        db,
        payload.product_id,
        payload.warehouse_id,
        payload.partner_id,
        payload.quantity
    )

    product_label = _resolve_product_label(db, payload.product_id)
    warehouse_label = _resolve_warehouse_label(db, payload.warehouse_id)
    partner_label = _resolve_partner_label(db, payload.partner_id)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=(
            f"Sortie stock: produit {product_label}, "
            f"entrepot {warehouse_label}, "
            f"partenaire {partner_label}, "
            f"quantite {payload.quantity}"
        ),
        type=NotificationType.WARNING,
        reference_id=payload.product_id
    )

    return result

@router.post("/transfer")
def create_transfer(
    payload: StockTransfer,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = stock_transfer(
        db,
        payload.product_id,
        payload.from_warehouse_id,
        payload.to_warehouse_id,
        payload.partner_id,
        payload.quantity
    )

    product_label = _resolve_product_label(db, payload.product_id)
    from_warehouse_label = _resolve_warehouse_label(db, payload.from_warehouse_id)
    to_warehouse_label = _resolve_warehouse_label(db, payload.to_warehouse_id)
    partner_label = _resolve_partner_label(db, payload.partner_id)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=(
            f"Transfert stock: produit {product_label}, "
            f"depot {from_warehouse_label} vers {to_warehouse_label}, "
            f"partenaire {partner_label}, "
            f"quantite {payload.quantity}"
        ),
        type=NotificationType.INFO,
        reference_id=payload.product_id
    )

    return result

@router.post("/transfer-to-project")
def create_transfer_to_project(
    payload: StockTransferToProject,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = stock_transfer_to_project(
        db,
        payload.product_id,
        payload.from_warehouse_id,
        payload.project_id,
        payload.quantity
    )

    product_label = _resolve_product_label(db, payload.product_id)
    warehouse_label = _resolve_warehouse_label(db, payload.from_warehouse_id)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=(
            f"Transfert vers projet: produit {product_label}, "
            f"depuis {warehouse_label}, "
            f"projet {payload.project_id}, "
            f"quantite {payload.quantity}"
        ),
        type=NotificationType.INFO,
        reference_id=payload.product_id
    )

    return result
