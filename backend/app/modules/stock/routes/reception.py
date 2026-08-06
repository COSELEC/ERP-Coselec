from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import BackgroundTasks
from app.services.event_notifier import notify_users_by_role
from app.models.notification import NotificationType

from app.core.database import get_db
from app.modules.stock.models.reception import ReceptionControl, ReceptionControlLine
from app.models.procurement.purchase import PurchaseOrder
from app.models.project.expense import ProjectExpense
from app.services.pdf_generator import generate_reception_control_pdf

router = APIRouter(prefix="/receptions", tags=["reception"])

class ReceptionLinePayload(BaseModel):
    product_id: Optional[int]
    designation: str
    qty_ordered: int
    qty_delivered: int
    is_compliant: bool
    notes: Optional[str]

class ReceptionPayload(BaseModel):
    po_id: Optional[int]
    supplier_id: Optional[int]
    created_by: Optional[int]
    stock_type: Optional[str] = "GENERAL"
    project_id: Optional[int] = None
    lines: List[ReceptionLinePayload]

@router.post("")
def create_reception(payload: ReceptionPayload, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Create Reception
    reception = ReceptionControl(
        po_id=payload.po_id,
        supplier_id=payload.supplier_id,
        created_by=payload.created_by,
        stock_type=payload.stock_type,
        project_id=payload.project_id,
        delivery_date=datetime.utcnow()
    )
    db.add(reception)
    db.commit()
    db.refresh(reception)
    
    total_expense = 0.0
    
    # 2. Add Lines
    for line_payload in payload.lines:
        line = ReceptionControlLine(
            reception_id=reception.id,
            product_id=line_payload.product_id,
            designation=line_payload.designation,
            qty_ordered=line_payload.qty_ordered,
            qty_delivered=line_payload.qty_delivered,
            is_compliant=line_payload.is_compliant,
            notes=line_payload.notes
        )
        db.add(line)
        
        # Calculate expense if there is a PO
        if payload.po_id and line_payload.is_compliant:
            # We don't have unit prices mapped easily here unless we query PO lines, 
            # but for simplicity, we assume an expense will be logged if project is tied.
            # In a real scenario, we'd lookup unit price from PO.
            pass
            
    db.commit()
    
    # 3. Handle Project Expense if PO exists
    if payload.po_id:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == payload.po_id).first()
        if po and po.project_id:
            # Calculate total cost from PO lines
            # This is simplified; ideally it's based on actual delivered qty * unit_price
            for po_line in po.lines:
                # Find matching reception line
                rec_line = next((rl for rl in payload.lines if rl.designation == po_line.designation), None)
                if rec_line and rec_line.is_compliant:
                    total_expense += (rec_line.qty_delivered * po_line.unit_price)
            
            if total_expense > 0:
                expense = ProjectExpense(
                    project_id=po.project_id,
                    amount=total_expense,
                    description=f"Réception de matériel - Bon de commande {po.reference}",
                    expense_date=datetime.utcnow()
                )
                db.add(expense)
                db.commit()
    
    # 4. Generate PDF
    # pdf_url = generate_reception_control_pdf(reception.id, db)
    # reception.pdf_url = pdf_url
    # db.commit()
    
    background_tasks.add_task(
        notify_users_by_role,
        ["Admin", "Achat", "Stock"],
        f"Nouvelle réception enregistrée (BC: {payload.po_id or 'N/A'}).",
        NotificationType.INFO,
        reception.id
    )
    
    return {"message": "Réception enregistrée avec succès", "reception_id": reception.id}
