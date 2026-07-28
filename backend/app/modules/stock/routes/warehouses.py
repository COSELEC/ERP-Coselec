from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.stock.models.warehouse import Warehouse
from app.modules.users.models.user import User

from app.modules.stock.schemas.warehouse import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate
)

router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouses"]
)


@router.post(
    "/",
    response_model=WarehouseResponse
)
def create_warehouse(
    warehouse: WarehouseCreate,
    _: None = Depends(check_permission("stock.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    existing = (
        db.query(Warehouse)
        .filter(Warehouse.code == warehouse.code)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Warehouse already exists"
        )

    new_warehouse = Warehouse(
        **warehouse.model_dump()
    )

    db.add(new_warehouse)
    db.commit()
    db.refresh(new_warehouse)

    return new_warehouse


@router.get(
    "/",
    response_model=list[WarehouseResponse]
)
def get_warehouses(
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return db.query(Warehouse).all()


@router.get("/{warehouse_id}", response_model=WarehouseResponse, status_code=status.HTTP_200_OK)
def get_warehouse(warehouse_id: int,_:None = Depends(check_permission("stock.read")), current_user : User = Depends(get_current_user), db: Session = Depends(get_db)):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if warehouse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dépôt non trouvé")
    return warehouse

@router.put(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK
)
def update_warehouse(
    warehouse_id: int,
    warehouse: WarehouseUpdate,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_warehouse = (
        db.query(Warehouse)
        .filter(Warehouse.id == warehouse_id)
        .first()
    )

    if not db_warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dépôt non trouvé"
        )

    if warehouse.code and warehouse.code != db_warehouse.code:
        existing = (
            db.query(Warehouse)
            .filter(Warehouse.code == warehouse.code)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le code du dépôt existe déjà"
            )

    update_data = warehouse.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_warehouse, field, value)

    db.commit()
    db.refresh(db_warehouse)

    return db_warehouse

@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(
    warehouse_id: int,
    _: None = Depends(check_permission("stock.delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    warehouse = db.get(Warehouse, warehouse_id)

    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    if warehouse.stock_movements:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Warehouse cannot be deleted because it contains inventory history.",
    )

    db.delete(warehouse)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
