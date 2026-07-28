from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.modules.stock.models.reservation import ProjectStockReservation, ReservationStatus
from app.modules.stock.models.stock import Stock
from app.modules.stock.models.product import Product
from pydantic import BaseModel, ConfigDict, computed_field, Field
from datetime import datetime
from typing import List, Optional
from sqlalchemy import or_, cast, String

router = APIRouter(prefix="/stock-reservations", tags=["Stock Reservations"])

class ReservationCreate(BaseModel):
    project_id: int
    product_id: int
    reserved_by_id: int | None = None
    quantity: int = Field(..., gt=0)

class ReservationResponse(ReservationCreate):
    id: int
    status: str
    created_at: datetime
    consumed_at: datetime | None = None
    
    @computed_field
    def product_name(self) -> str | None:
        return self.product.name if getattr(self, "product", None) else None

    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[ReservationResponse])
def get_reservations(
    search: Optional[str] = None, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    query = db.query(ProjectStockReservation).join(Product, ProjectStockReservation.product_id == Product.id).options(joinedload(ProjectStockReservation.product))
    if search:
        if search.isdigit():
            query = query.filter(
                or_(
                    ProjectStockReservation.id == int(search),
                    ProjectStockReservation.project_id == int(search)
                )
            )
        else:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.code.ilike(search_term),
                    Product.designation.ilike(search_term)
                )
            )
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=ReservationResponse)
def create_reservation(res: ReservationCreate, db: Session = Depends(get_db)):
    stock = db.query(Stock).with_for_update().filter(Stock.product_id == res.product_id).first()
    
    if not stock or stock.quantity < res.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock available for reservation")
        
    db_res = ProjectStockReservation(
        project_id=res.project_id,
        product_id=res.product_id,
        reserved_by_id=res.reserved_by_id,
        quantity=res.quantity
    )
    db.add(db_res)
    
    # Deduct available stock
    stock.quantity -= res.quantity
    
    try:
        db.commit()
        db.refresh(db_res)
        return db_res
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Identifiant invalide (projet, produit ou employé introuvable)")

@router.post("/{reservation_id}/consume", response_model=ReservationResponse)
def consume_reservation(reservation_id: int, db: Session = Depends(get_db)):
    db_res = db.query(ProjectStockReservation).filter(ProjectStockReservation.id == reservation_id).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Reservation not found")
        
    if db_res.status != ReservationStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Reservation must be APPROVED to be consumed")
        
    db_res.status = ReservationStatus.CONSUMED
    db_res.consumed_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_res)
        return db_res
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Impossible de consommer la réservation")

@router.post("/{reservation_id}/approve", response_model=ReservationResponse)
def approve_reservation(reservation_id: int, db: Session = Depends(get_db)):
    db_res = db.query(ProjectStockReservation).filter(ProjectStockReservation.id == reservation_id).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Reservation not found")
        
    if db_res.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING reservations can be approved")
        
    db_res.status = ReservationStatus.APPROVED
    db.commit()
    db.refresh(db_res)
    return db_res

@router.post("/{reservation_id}/reject", response_model=ReservationResponse)
def reject_reservation(reservation_id: int, db: Session = Depends(get_db)):
    db_res = db.query(ProjectStockReservation).filter(ProjectStockReservation.id == reservation_id).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Reservation not found")
        
    if db_res.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING reservations can be rejected")
        
    # Restore stock
    stock = db.query(Stock).with_for_update().filter(Stock.product_id == db_res.product_id).first()
    if stock:
        stock.quantity += db_res.quantity

    db_res.status = ReservationStatus.CANCELLED
    db.commit()
    db.refresh(db_res)
    return db_res
