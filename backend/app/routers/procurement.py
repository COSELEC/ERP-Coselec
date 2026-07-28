from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.security.auth import check_permission
from app.modules.users.models.user import User
from app.models.procurement.purchase import PurchaseRequest, PurchaseOrder, PurchaseOrderLine
from app.services.pdf_generator import generate_purchase_order_pdf
from app.services.storage import get_file_url_from_minio
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import or_, cast, String

router = APIRouter(prefix="/procurement", tags=["Procurement"])

class PurchaseRequestCreate(BaseModel):
    project_id: int
    requester_id: int | None = None
    description: str | None = None
    expected_date: date | None = None

class PurchaseRequestResponse(PurchaseRequestCreate):
    id: int
    status: str
    model_config = ConfigDict(from_attributes=True)

class PurchaseOrderLineCreate(BaseModel):
    product_id: int | None = None
    designation: str | None = None
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)

class PurchaseOrderCreate(BaseModel):
    purchase_request_id: int | None = None
    supplier_id: int | None = None
    lines: List[PurchaseOrderLineCreate] = []

class PurchaseOrderResponse(PurchaseOrderCreate):
    id: int
    reference: str | None = None
    generic_request_id: int | None = None
    project_id: int | None = None
    pdf_url: str | None = None
    status: str
    total_amount: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

@router.get("/requests/", response_model=List[PurchaseRequestResponse])
def get_purchase_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.read")),
):
    return db.query(PurchaseRequest).all()

@router.post("/requests/", response_model=PurchaseRequestResponse)
def create_purchase_request(
    req: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.create")),
):
    db_req = PurchaseRequest(
        project_id=req.project_id,
        requester_id=req.requester_id,
        description=req.description,
        expected_date=req.expected_date
    )
    db.add(db_req)
    try:
        db.commit()
        db.refresh(db_req)
        return db_req
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid project_id or requester_id")

@router.get("/orders/", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.read")),
):
    query = db.query(PurchaseOrder)
    if search:
        search_term_bc = search.replace("BC-", "")
        search_term_da = search.replace("DA-", "")
        query = query.filter(
            or_(
                cast(PurchaseOrder.id, String).ilike(f"%{search_term_bc}%"),
                cast(PurchaseOrder.purchase_request_id, String).ilike(f"%{search_term_da}%"),
                cast(PurchaseOrder.created_at, String).ilike(f"%{search}%")
            )
        )
    return query.all()

@router.post("/orders/", response_model=PurchaseOrderResponse)
def create_purchase_order(
    order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.create")),
):
    db_order = PurchaseOrder(
        purchase_request_id=order.purchase_request_id,
        supplier_id=order.supplier_id,
        total_amount=0.0
    )
    db.add(db_order)
    
    try:
        db.flush() # Flush to get db_order.id
        
        total = 0.0
        for line in order.lines:
            db_line = PurchaseOrderLine(
                purchase_order_id=db_order.id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price
            )
            db.add(db_line)
            total += (line.quantity * line.unit_price)
            
        db_order.total_amount = total
        db.commit()
        db.refresh(db_order)
        return db_order
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid request_id, supplier_id or product_id")

@router.get("/orders/{order_id}/download-pdf")
def download_order_pdf(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.read")),
):
    db_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if not db_order.pdf_url:
        pdf_path = generate_purchase_order_pdf(db_order)
        if pdf_path:
            db_order.pdf_url = pdf_path
            db.commit()
        else:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
            
    url = get_file_url_from_minio(db_order.pdf_url)
    return {"pdf_url": url}
