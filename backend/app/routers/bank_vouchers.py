from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.models.caisse_voucher import CaisseVoucher
from app.models.bank_voucher import BankVoucher, AnalyticalAllocation
from app.services.pdf_generator import generate_bank_voucher_pdf
from app.services.storage import get_file_url_from_minio, upload_file_to_minio
from app.models.voucher_attachment import VoucherAttachment
from fastapi import UploadFile, File
import uuid

from app.core.security.auth import require_rh_role

router = APIRouter(
    prefix="/bank-vouchers", 
    tags=["Bank Vouchers"],
    dependencies=[Depends(require_rh_role)]
)

class AnalyticalAllocationCreate(BaseModel):
    cost_center_code: str
    cost_center_name: str
    client: Optional[str] = None
    analytical_account: str
    amount: float = Field(..., gt=0)

class BankVoucherCreate(BaseModel):
    bank_name: str
    check_number: str
    date: date
    period_num: str
    description: str
    recipient: str
    amount_in_numbers: float = Field(..., gt=0)
    currency: str = "FCFA"
    amount_in_letters: str
    allocations: List[AnalyticalAllocationCreate]
    project_id: Optional[int] = None
    expense_id: Optional[int] = None
    reservation_id: Optional[int] = None
    linked_caisse_voucher_ids: List[int] = []

from fastapi.responses import RedirectResponse

@router.get("", status_code=status.HTTP_200_OK)
def get_bank_vouchers(
    search: Optional[str] = None, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    query = db.query(BankVoucher)
    if search:
        if search.isdigit():
            query = query.filter(BankVoucher.id == int(search))
        else:
            search_term = f"%{search}%"
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    BankVoucher.bank_name.ilike(search_term),
                    BankVoucher.check_number.ilike(search_term),
                    BankVoucher.recipient.ilike(search_term),
                    BankVoucher.description.ilike(search_term)
                )
            )
    vouchers = query.order_by(BankVoucher.id.desc()).offset(skip).limit(limit).all()
    results = []
    for v in vouchers:
        results.append({
            "id": v.id,
            "bank_name": v.bank_name,
            "check_number": v.check_number,
            "date": v.date,
            "period_num": v.period_num,
            "description": v.description,
            "recipient": v.recipient,
            "status": v.status,
            "finalized_at": v.finalized_at,
            "amount_in_numbers": float(v.amount_in_numbers) if v.amount_in_numbers is not None else 0.0,
            "currency": v.currency,
            "amount_in_letters": v.amount_in_letters,
            "pdf_url": get_file_url_from_minio(v.pdf_url) if v.pdf_url else None,
            "linked_caisse_voucher_ids": v.linked_caisse_voucher_ids or [],
            "project_id": v.project_id,
            "expense_id": v.expense_id,
            "reservation_id": v.reservation_id,
        })
    return results

@router.get("/next-id", status_code=status.HTTP_200_OK)
def get_next_bank_voucher_id(db: Session = Depends(get_db)):
    last_voucher = db.query(BankVoucher).order_by(BankVoucher.id.desc()).first()
    next_id = last_voucher.id + 1 if last_voucher else 1
    return {"next_id": next_id}

@router.get("/{voucher_id}/pdf")
def get_bank_voucher_pdf_url(voucher_id: int, db: Session = Depends(get_db)):
    voucher = db.query(BankVoucher).filter(BankVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Pièce de banque non trouvée")
        
    if not voucher.pdf_url:
        allocations = db.query(AnalyticalAllocation).filter(AnalyticalAllocation.bank_voucher_id == voucher.id).all()
        pdf_filename = generate_bank_voucher_pdf(voucher, allocations)
        if pdf_filename:
            voucher.pdf_url = pdf_filename
            db.commit()
            db.refresh(voucher)

    if not voucher.pdf_url:
        raise HTTPException(status_code=404, detail="PDF non disponible")
        
    url = get_file_url_from_minio(voucher.pdf_url)
    return RedirectResponse(url=url)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_bank_voucher(voucher_in: BankVoucherCreate, db: Session = Depends(get_db)):
    if not voucher_in.allocations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="La pièce de banque doit comporter au moins une ligne d'imputation analytique."
        )
    
    total_allocation = sum(alloc.amount for alloc in voucher_in.allocations)
    if abs(total_allocation - voucher_in.amount_in_numbers) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le total des imputations ({total_allocation}) ne correspond pas au montant du chèque ({voucher_in.amount_in_numbers})."
        )
        
    db_bank_voucher = BankVoucher(
        bank_name=voucher_in.bank_name,
        check_number=voucher_in.check_number,
        date=voucher_in.date,
        period_num=voucher_in.period_num,
        description=voucher_in.description,
        recipient=voucher_in.recipient,
        amount_in_numbers=voucher_in.amount_in_numbers,
        currency=voucher_in.currency,
        amount_in_letters=voucher_in.amount_in_letters,
        project_id=voucher_in.project_id,
        expense_id=voucher_in.expense_id,
        reservation_id=voucher_in.reservation_id,
        linked_caisse_voucher_ids=voucher_in.linked_caisse_voucher_ids
    )
    db.add(db_bank_voucher)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce numéro de chèque existe déjà. Veuillez en utiliser un autre."
        )
    
    for alloc_in in voucher_in.allocations:
        db_alloc = AnalyticalAllocation(bank_voucher_id=db_bank_voucher.id, **alloc_in.model_dump())
        db.add(db_alloc)
    
    pdf_filename = None
    try:
        db.flush()
        pdf_filename = generate_bank_voucher_pdf(db_bank_voucher, voucher_in.allocations)
        if pdf_filename:
            db_bank_voucher.pdf_url = pdf_filename
    except Exception as e:
        print(f"Erreur PDF : {e}")

    db.commit()
    db.refresh(db_bank_voucher)

    fresh_pdf_url = get_file_url_from_minio(db_bank_voucher.pdf_url) if db_bank_voucher.pdf_url else None

    return {
        "id": db_bank_voucher.id,
        "bank_name": db_bank_voucher.bank_name,
        "check_number": db_bank_voucher.check_number,
        "date": db_bank_voucher.date,
        "period_num": db_bank_voucher.period_num,
        "description": db_bank_voucher.description,
        "recipient": db_bank_voucher.recipient,
        "status": db_bank_voucher.status,
        "amount_in_numbers": float(db_bank_voucher.amount_in_numbers),
        "currency": db_bank_voucher.currency,
        "amount_in_letters": db_bank_voucher.amount_in_letters,
        "pdf_url": fresh_pdf_url,
        "linked_caisse_voucher_ids": db_bank_voucher.linked_caisse_voucher_ids or [],
        "project_id": db_bank_voucher.project_id,
        "expense_id": db_bank_voucher.expense_id,
        "reservation_id": db_bank_voucher.reservation_id,
    }

@router.post("/{voucher_id}/finalize")
def finalize_bank_voucher(voucher_id: int, db: Session = Depends(get_db)):
    from app.models.caisse_voucher import VoucherStatus
    from app.models.project.expense import ProjectExpense, ExpenseStatus
    from datetime import datetime
    voucher = db.query(BankVoucher).filter(BankVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
        
    if voucher.status != VoucherStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT vouchers can be finalized")
        
    voucher.status = VoucherStatus.FINALIZED
    voucher.finalized_at = datetime.utcnow()

    if voucher.expense_id:
        expense = db.query(ProjectExpense).filter(ProjectExpense.id == voucher.expense_id).first()
        if expense:
            expense.status = ExpenseStatus.APPROVED
            expense.amount = voucher.amount_in_numbers

    db.commit()
    db.refresh(voucher)
    return {"status": voucher.status, "finalized_at": voucher.finalized_at}

@router.post("/{voucher_id}/void")
def void_bank_voucher(voucher_id: int, db: Session = Depends(get_db)):
    from app.models.caisse_voucher import VoucherStatus
    voucher = db.query(BankVoucher).filter(BankVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
        
    if voucher.status == VoucherStatus.VOID:
        raise HTTPException(status_code=400, detail="Voucher is already voided")
        
    voucher.status = VoucherStatus.VOID
    db.commit()
    db.refresh(voucher)
    return {"status": voucher.status}

@router.post("/{voucher_id}/attachments")
def upload_bank_attachment(
    voucher_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    voucher = db.query(BankVoucher).filter(BankVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Bank Voucher not found")
        
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    filename = f"orders/bank_{voucher_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    try:
        storage_path = upload_file_to_minio(file, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        
    attachment = VoucherAttachment(
        bank_voucher_id=voucher_id,
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
def get_bank_attachments(voucher_id: int, db: Session = Depends(get_db)):
    attachments = db.query(VoucherAttachment).filter(VoucherAttachment.bank_voucher_id == voucher_id).all()
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
