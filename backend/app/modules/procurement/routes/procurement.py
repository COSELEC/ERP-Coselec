from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.security.auth import check_permission
from app.modules.users.models.user import User
from app.models.procurement.purchase import PurchaseRequest, PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from app.models.project.expense import ProjectExpense, ExpenseStatus
from app.services.pdf_generator import generate_purchase_order_pdf
from app.services.storage import get_file_url_from_minio
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import or_, cast, String
from fastapi import BackgroundTasks
from app.services.event_notifier import notify_users_by_role
from app.models.notification import NotificationType

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

class PurchaseOrderLineResponse(PurchaseOrderLineCreate):
    id: int
    budget_id: int | None = None
    model_config = ConfigDict(from_attributes=True)

class PurchaseOrderResponse(PurchaseOrderCreate):
    id: int
    reference: str | None = None
    generic_request_id: int | None = None
    project_id: int | None = None
    pdf_url: str | None = None
    status: str
    total_amount: float
    created_at: datetime
    lines: List[PurchaseOrderLineResponse] = []
    model_config = ConfigDict(from_attributes=True)

class PurchaseOrderLineApprove(BaseModel):
    line_id: int
    budget_id: int | None = None

class PurchaseOrderApproveRequest(BaseModel):
    lines: List[PurchaseOrderLineApprove]

@router.get("/requests", response_model=List[PurchaseRequestResponse])
def get_purchase_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.read")),
):
    return db.query(PurchaseRequest).all()

@router.post("/requests", response_model=PurchaseRequestResponse)
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
        raise HTTPException(status_code=400, detail="project_id ou requester_id invalide")

@router.get("/orders", response_model=List[PurchaseOrderResponse])
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

@router.post("/orders", response_model=PurchaseOrderResponse)
def create_purchase_order(
    order: PurchaseOrderCreate,
    background_tasks: BackgroundTasks,
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
        db.flush() 
        
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
        
        background_tasks.add_task(
            notify_users_by_role,
            ["Admin", "Finance", "Achat"],
            f"Nouveau bon de commande #{db_order.id} créé et en attente de validation.",
            NotificationType.INFO,
            db_order.id
        )

        return db_order
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="request_id, supplier_id ou product_id invalide")

@router.get("/orders/{order_id}/download-pdf")
def download_order_pdf(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.read")),
):
    db_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
        
    if not db_order.pdf_url:
        pdf_path = generate_purchase_order_pdf(db_order)
        if pdf_path:
            db_order.pdf_url = pdf_path
            db.commit()
        else:
            raise HTTPException(status_code=500, detail="Échec de la génération du PDF")
            
    url = get_file_url_from_minio(db_order.pdf_url)
    return {"pdf_url": url}

@router.put("/orders/{order_id}/approve", response_model=PurchaseOrderResponse)
def approve_purchase_order(
    order_id: int,
    approve_req: PurchaseOrderApproveRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.create")),
):
    db_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
        
    if getattr(db_order.status, "name", db_order.status) == "APPROVED":
        raise HTTPException(status_code=400, detail="La commande est déjà approuvée")
        
    line_map = {line.id: line for line in db_order.lines}
    
    proj_id = db_order.project_id
    if not proj_id and db_order.purchase_request:
        proj_id = db_order.purchase_request.project_id
        
    if not proj_id:
        raise HTTPException(status_code=400, detail="La commande n'est liée à aucun projet")
    
    for approve_line in approve_req.lines:
        db_line = line_map.get(approve_line.line_id)
        if db_line:
            db_line.budget_id = approve_line.budget_id
            
            expense = ProjectExpense(
                project_id=proj_id,
                budget_id=approve_line.budget_id,
                purchase_order_line_id=db_line.id,
                amount=db_line.quantity * db_line.unit_price,
                date_incurred=datetime.utcnow().date(),
                description=f"Achat: {db_line.designation} (BC {db_order.reference or db_order.id})",
                status=ExpenseStatus.APPROVED
            )
            db.add(expense)
            
    db_order.status = PurchaseOrderStatus.APPROVED
    
    try:
        db.commit()
        db.refresh(db_order)
        
        background_tasks.add_task(
            notify_users_by_role,
            ["Admin", "Achat"],
            f"Le bon de commande #{db_order.id} a été approuvé.",
            NotificationType.INFO,
            db_order.id
        )

        return db_order
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class DeliveryNoteLineUpdate(BaseModel):
    id: int
    delivered_quantity: float
    is_compliant: bool
    notes: Optional[str] = None

class DeliveryNoteApproveRequest(BaseModel):
    lines: List[DeliveryNoteLineUpdate]
    comments: Optional[str] = None
    action: str 

class DeliveryNoteLineResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    designation: Optional[str] = None
    ordered_quantity: float
    delivered_quantity: float
    is_compliant: bool
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DeliveryNoteResponse(BaseModel):
    id: int
    reference: str
    purchase_order_id: int
    supplier_name: Optional[str] = None
    created_at: datetime
    status: str
    magasinier_validator_id: Optional[int] = None
    magasinier_validated_at: Optional[datetime] = None
    manager_validator_id: Optional[int] = None
    manager_validated_at: Optional[datetime] = None
    lines: List[DeliveryNoteLineResponse] = []
    model_config = ConfigDict(from_attributes=True)

@router.get("/delivery-notes", response_model=List[DeliveryNoteResponse])
def get_delivery_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.read")),
):
    from app.models.procurement.delivery import DeliveryNote
    return db.query(DeliveryNote).order_by(DeliveryNote.created_at.desc()).all()

@router.post("/delivery-notes/{note_id}/validate", response_model=DeliveryNoteResponse)
def validate_delivery_note(
    note_id: int,
    req: DeliveryNoteApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("stock.create")),
):
    from app.models.procurement.delivery import DeliveryNote, DeliveryNoteStatus, DeliveryNoteLine
    
    note = db.query(DeliveryNote).filter(DeliveryNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Bon de livraison introuvable")
        
    for line_req in req.lines:
        line = db.query(DeliveryNoteLine).filter(DeliveryNoteLine.id == line_req.id, DeliveryNoteLine.delivery_note_id == note.id).first()
        if line:
            line.delivered_quantity = line_req.delivered_quantity
            line.is_compliant = line_req.is_compliant
            line.notes = line_req.notes
            
    if req.action == "magasinier":
        if note.status != DeliveryNoteStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Le bon de livraison n'est pas au statut BROUILLON")
        note.status = DeliveryNoteStatus.CHECKED_BY_MAGASINIER
        note.magasinier_validator_id = current_user.id
        note.magasinier_validated_at = datetime.utcnow()
    elif req.action == "manager":
        if note.status != DeliveryNoteStatus.CHECKED_BY_MAGASINIER:
            raise HTTPException(status_code=400, detail="Le bon de livraison doit d'abord être vérifié par le magasinier")
        note.status = DeliveryNoteStatus.VALIDATED_BY_MANAGER
        note.manager_validator_id = current_user.id
        note.manager_validated_at = datetime.utcnow()
        
    db.commit()
    db.refresh(note)
    return note
