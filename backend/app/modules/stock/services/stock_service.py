from fastapi import HTTPException

from app.modules.stock.models.partner import Partner
from app.modules.stock.models.stock import Stock
from app.modules.stock.models.stockmovement import StockMovement
from app.modules.stock.models.warehouse import Warehouse

from app.modules.stock.enums.movement_type import MovementType


def get_or_create_internal_partner(db):
    partners = db.query(Partner).all()

    internal_partner = next(
        (
            partner for partner in partners
            if (
                (partner.name or "").strip().lower().find("coselec") != -1
                or (partner.code or "").strip().lower() in {"coselec", "internal", "int", "coselec_internal"}
            )
        ),
        None
    )

    if internal_partner:
        return internal_partner

    created_partner = Partner(
        code="COSELEC_INTERNAL",
        name="Coselec Interne"
    )
    db.add(created_partner)
    db.flush()
    return created_partner


def resolve_partner_id(db, partner_id):
    if partner_id:
        return partner_id

    return get_or_create_internal_partner(db).id


def get_magasin_warehouse(db):
    warehouses = db.query(Warehouse).all()

    return next(
        (
            warehouse for warehouse in warehouses
            if (
                (warehouse.code or "").strip().upper() == "MAG"
                or (warehouse.name or "").strip().lower() == "magasin"
            )
        ),
        None
    )


def get_or_create_stock(
    db,
    product_id,
    warehouse_id,
    partner_id
):
    stock = (
        db.query(Stock)
        .with_for_update()
        .filter(
            Stock.product_id == product_id,
            Stock.warehouse_id == warehouse_id,
            Stock.partner_id == partner_id
        )
        .first()
    )

    if not stock:
        stock = Stock(
            product_id=product_id,
            warehouse_id=warehouse_id,
            partner_id=partner_id,
            quantity=0
        )

        db.add(stock)
        db.flush()

    return stock

def stock_entry(
    db,
    product_id,
    warehouse_id,
    partner_id,
    quantity
):
    resolved_partner_id = resolve_partner_id(
        db,
        partner_id
    )

    internal_partner_id = get_or_create_internal_partner(db).id
    magasin_warehouse = get_magasin_warehouse(db)
    is_internal_movement = (
        partner_id is None or resolved_partner_id == internal_partner_id
    )

    destination_stock = get_or_create_stock(
        db,
        product_id,
        warehouse_id,
        resolved_partner_id
    )

    if is_internal_movement and magasin_warehouse and warehouse_id != magasin_warehouse.id:
        magasin_stock = get_or_create_stock(
            db,
            product_id,
            magasin_warehouse.id,
            internal_partner_id
        )

        if magasin_stock.quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail="Pas assez de stock dans le magasin"
            )

        magasin_stock.quantity -= quantity
        destination_stock.quantity += quantity
    else:
        destination_stock.quantity += quantity

    movement = StockMovement(
        product_id=product_id,
        warehouse_id=warehouse_id,
        partner_id=resolved_partner_id,
        quantity=quantity,
        type=MovementType.ENTRY
    )

    db.add(movement)

    db.commit()

    return destination_stock

def stock_exit(
    db,
    product_id,
    warehouse_id,
    partner_id,
    quantity
):
    resolved_partner_id = resolve_partner_id(
        db,
        partner_id
    )

    stock = get_or_create_stock(
        db,
        product_id,
        warehouse_id,
        resolved_partner_id
    )

    if stock.quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    stock.quantity -= quantity

    movement = StockMovement(
        product_id=product_id,
        warehouse_id=warehouse_id,
        partner_id=resolved_partner_id,
        quantity=quantity,
        type=MovementType.EXIT
    )

    db.add(movement)

    db.commit()

    return stock

def stock_transfer(
    db,
    product_id,
    from_warehouse_id,
    to_warehouse_id,
    partner_id,
    quantity
):
    origin = get_or_create_stock(
        db,
        product_id,
        from_warehouse_id,
        partner_id
    )

    if origin.quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    destination = get_or_create_stock(
        db,
        product_id,
        to_warehouse_id,
        partner_id
    )

    origin.quantity -= quantity
    destination.quantity += quantity

    db.add(
        StockMovement(
            product_id=product_id,
            warehouse_id=from_warehouse_id,
            partner_id=partner_id,
            quantity=quantity,
            type=MovementType.TRANSFER_OUT
        )
    )

    db.add(
        StockMovement(
            product_id=product_id,
            warehouse_id=to_warehouse_id,
            partner_id=partner_id,
            quantity=quantity,
            type=MovementType.TRANSFER_IN
        )
    )

    db.commit()

    return {
        "message": "Transfer completed"
    }
