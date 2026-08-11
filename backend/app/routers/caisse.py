from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from pydantic import BaseModel, ConfigDict, computed_field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import or_
from app.services.pdf_generator import generate_caisse_pdf
from app.services.storage import get_file_url_from_minio
from app.models.caisse_voucher import CaisseVoucher, CaisseVoucherLine, CaisseVoucherLineType
from app.models.voucher_attachment import VoucherAttachment
from fastapi import UploadFile, File, HTTPException
import uuid
from app.services.storage import upload_file_to_minio

from app.core.security.auth import require_rh_role

router = APIRouter(
    prefix="/caisse",
    tags=["Caisse"],
    dependencies=[Depends(require_rh_role)]
)

class CaisseRow(BaseModel):
    date: str
    designation: str
    montant: str

class CaisseRequest(BaseModel):
    num: Optional[str] = ""
    affaire: Optional[str] = ""
    cia: Optional[str] = ""
    payment_method: Optional[str] = None
    depenses: List[CaisseRow] = []
    recettes: List[CaisseRow] = []
    project_id: Optional[int] = None
    expense_id: Optional[int] = None
    reservation_id: Optional[int] = None

class CaisseVoucherResponse(BaseModel):
    id: int
    num: Optional[str]
    affaire: Optional[str]
    cia: Optional[str]
    payment_method: Optional[str] = None
    pdf_url: Optional[str]
    created_at: datetime
    
    @computed_field
    def depenses(self) -> List[CaisseRow]:
        if not getattr(self, "lines", None):
            return []
        return [CaisseRow(date=str(l.date), designation=l.designation, montant=str(l.amount)) for l in self.lines if l.line_type.value == "EXPENSE"]

    @computed_field
    def recettes(self) -> List[CaisseRow]:
        if not getattr(self, "lines", None):
            return []
        return [CaisseRow(date=str(l.date), designation=l.designation, montant=str(l.amount)) for l in self.lines if l.line_type.value == "RECEIPT"]

    model_config = ConfigDict(from_attributes=True)

from fastapi.responses import RedirectResponse

@router.get("", response_model=List[CaisseVoucherResponse])
def get_caisse_vouchers(
    search: Optional[str] = None, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    query = db.query(CaisseVoucher)
    if search:
        if search.isdigit():
            query = query.filter(CaisseVoucher.id == int(search))
        else:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    CaisseVoucher.num.ilike(search_term),
                    CaisseVoucher.affaire.ilike(search_term),
                    CaisseVoucher.cia.ilike(search_term)
                )
            )
    vouchers = query.order_by(CaisseVoucher.id.desc()).offset(skip).limit(limit).all()
    results = []
    for v in vouchers:
        v_dict = CaisseVoucherResponse.model_validate(v).model_dump()
        if v.pdf_url:
            v_dict["pdf_url"] = get_file_url_from_minio(v.pdf_url)
        results.append(CaisseVoucherResponse(**v_dict))
    return results

@router.get("/{voucher_id}/pdf")
def get_caisse_voucher_pdf_url(voucher_id: int, db: Session = Depends(get_db)):
    voucher = db.query(CaisseVoucher).filter(CaisseVoucher.id == voucher_id).first()
    if not voucher or not voucher.pdf_url:
        raise HTTPException(status_code=404, detail="PDF non trouvé")
    url = get_file_url_from_minio(voucher.pdf_url)
    return RedirectResponse(url=url)

@router.post("/generate")
def generate_caisse(payload: CaisseRequest, db: Session = Depends(get_db)):
    pdf_path = generate_caisse_pdf(payload.dict())
    if not pdf_path:
        return {"error": "Failed to generate PDF"}
        
    voucher = CaisseVoucher(
        num=payload.num,
        affaire=payload.affaire,
        cia=payload.cia,
        payment_method=payload.payment_method,
        pdf_url=pdf_path,
        project_id=payload.project_id,
        expense_id=payload.expense_id,
        reservation_id=payload.reservation_id
    )
    db.add(voucher)
    db.flush()
    
    for row in payload.depenses:
        line = CaisseVoucherLine(
            voucher_id=voucher.id,
            line_type=CaisseVoucherLineType.EXPENSE,
            date=row.date,
            designation=row.designation,
            amount=float(row.montant) if row.montant else 0.0
        )
        db.add(line)
        
    for row in payload.recettes:
        line = CaisseVoucherLine(
            voucher_id=voucher.id,
            line_type=CaisseVoucherLineType.RECEIPT,
            date=row.date,
            designation=row.designation,
            amount=float(row.montant) if row.montant else 0.0
        )
        db.add(line)
        
    db.commit()
    db.refresh(voucher)
    
    fresh_pdf_url = get_file_url_from_minio(pdf_path)
    return {"pdf_url": fresh_pdf_url, "voucher_id": voucher.id}

@router.post("/{voucher_id}/finalize")
def finalize_caisse(voucher_id: int, db: Session = Depends(get_db)):
    from app.models.caisse_voucher import VoucherStatus
    from app.models.project.expense import ProjectExpense, ExpenseStatus
    voucher = db.query(CaisseVoucher).filter(CaisseVoucher.id == voucher_id).first()
    if not voucher:
        return {"error": "Voucher not found"}
        
    if voucher.status != VoucherStatus.DRAFT:
        return {"error": "Only DRAFT vouchers can be finalized"}
        
    voucher.status = VoucherStatus.FINALIZED
    voucher.finalized_at = datetime.utcnow()
    
    if voucher.expense_id:
        expense = db.query(ProjectExpense).filter(ProjectExpense.id == voucher.expense_id).first()
        if expense:
            expense.status = ExpenseStatus.APPROVED
            total_expense = sum(float(l.amount) for l in voucher.lines if l.line_type.value == "EXPENSE")
            expense.amount = total_expense
            
    if voucher.generic_request_id:
        expense = db.query(ProjectExpense).filter(ProjectExpense.reference == f"REQ-{voucher.generic_request_id}").first()
        if expense:
            expense.status = "APPROVED"
            
        from app.models.procurement.purchase import PurchaseOrder, PurchaseOrderLine
        from app.modules.requests_unified.models.request import GenericRequest, RequestType
        import uuid
        
        request_obj = db.get(GenericRequest, voucher.generic_request_id)
        if request_obj and request_obj.type in (RequestType.FUEL, RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES):
            po = PurchaseOrder(
                reference=f"PO-{voucher.generic_request_id}-{uuid.uuid4().hex[:6]}".upper(),
                generic_request_id=voucher.generic_request_id,
                project_id=request_obj.project_id
            )
            db.add(po)
            db.flush()
            
            if request_obj.type == RequestType.FUEL:
                line = PurchaseOrderLine(
                    purchase_order_id=po.id,
                    designation=f"Carburant pour véhicule {request_obj.payload.get('vehicle_plate', '')}",
                    quantity=request_obj.payload.get("fuel_quantity", 1),
                    unit_price=0.0
                )
                db.add(line)
            else:
                items = request_obj.payload.get("items", [])
                for item in items:
                    line = PurchaseOrderLine(
                        purchase_order_id=po.id,
                        product_id=item.get("product_id"),
                        designation=item.get("designation", "Article inconnu"),
                        quantity=item.get("quantity", 1),
                        unit_price=0.0
                    )
                    db.add(line)
                    
            from app.models.procurement.delivery import DeliveryNote, DeliveryNoteLine
            
            delivery_note = DeliveryNote(
                reference=f"BL-{voucher.generic_request_id}-{uuid.uuid4().hex[:6]}".upper(),
                purchase_order_id=po.id,
                supplier_name=request_obj.payload.get("beneficiary", "Fournisseur inconnu")
            )
            db.add(delivery_note)
            db.flush()
            
            for item in po.lines:
                dl = DeliveryNoteLine(
                    delivery_note_id=delivery_note.id,
                    product_id=item.product_id,
                    designation=item.designation,
                    ordered_quantity=item.quantity,
                    delivered_quantity=0.0
                )
                db.add(dl)
                    
            from app.models.notification import Notification, NotificationType
            from app.modules.users.models.user import User
            
            rh_users = db.query(User).filter(User.roles.any(name="RH")).all()
            for rh in rh_users:
                notif = Notification(
                    user_id=rh.id,
                    message=f"La pièce de caisse #{voucher.id} a été validée. Merci de créer la pièce de banque correspondante pour le paiement.",
                    type=NotificationType.INFO.value,
                    reference_id=voucher.id
                )
                db.add(notif)
            
    db.commit()
    db.refresh(voucher)
    return {"status": voucher.status, "finalized_at": voucher.finalized_at}

@router.post("/{voucher_id}/void")
def void_caisse(voucher_id: int, db: Session = Depends(get_db)):
    from app.models.caisse_voucher import VoucherStatus
    voucher = db.query(CaisseVoucher).filter(CaisseVoucher.id == voucher_id).first()
    if not voucher:
        return {"error": "Voucher not found"}
        
    if voucher.status == VoucherStatus.VOID:
        return {"error": "Voucher is already voided"}
        
    voucher.status = VoucherStatus.VOID
    db.commit()
    db.refresh(voucher)
    return {"status": voucher.status}

@router.post("/{voucher_id}/attachments")
def upload_caisse_attachment(
    voucher_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    voucher = db.query(CaisseVoucher).filter(CaisseVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Caisse Voucher not found")
        
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    filename = f"orders/caisse_{voucher_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    try:
        storage_path = upload_file_to_minio(file, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        
    attachment = VoucherAttachment(
        caisse_voucher_id=voucher_id,
        file_name=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    url = get_file_url_from_minio(attachment.storage_path)
    return {"id": attachment.id, "file_name": attachment.file_name, "url": url}

@router.get("/{voucher_id}/attachments")
def get_caisse_attachments(voucher_id: int, db: Session = Depends(get_db)):
    attachments = db.query(VoucherAttachment).filter(VoucherAttachment.caisse_voucher_id == voucher_id).all()
    results = []
    for att in attachments:
        url = get_file_url_from_minio(att.storage_path)
        results.append({
            "id": att.id,
            "file_name": att.file_name,
            "mime_type": att.mime_type,
            "url": url,
            "created_at": att.created_at
        })
    return results
