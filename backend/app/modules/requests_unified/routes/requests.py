"""
Unified Requests Router
=======================
Handles all request types (HR, IT, Facility, Fuel, etc.) through a single
polymorphic API. Enforces state machine transitions, row-level security,
SLA deadlines, and writes immutable audit history.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security.auth import get_current_user, check_permission
from app.modules.users.models.user import User
from app.modules.requests_unified.models.request import (
    GenericRequest,
    RequestHistory,
    RequestStatus,
    RequestType,
    RequestPriority,
)
from app.modules.requests_unified.schemas.request import (
    RequestCreate,
    RequestUpdateStatus,
    RequestResponse,
)
from app.modules.requests_unified.services.state_machine import (
    validate_transition,
    initial_status_for,
    SLA_HOURS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/requests", tags=["Requests Unified"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_sla_deadline(priority: RequestPriority) -> datetime:
    hours = SLA_HOURS.get(priority.value, SLA_HOURS["NORMAL"])
    return datetime.utcnow() + timedelta(hours=hours)


def _record_history(
    db: Session,
    request: GenericRequest,
    old_status: str | None,
    new_status: str,
    user_id: int,
    comment: str | None = None,
) -> None:
    """Append an immutable audit entry to request_history."""
    db.add(RequestHistory(
        request_id=request.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=user_id,
        comment=comment,
    ))


def _user_roles(user: User) -> set[str]:
    return {role.name for role in user.roles}


def _apply_row_level_filter(query, current_user: User):
    """
    Enforce row-level security:
    - Admin sees everything
    - RH sees LEAVE requests
    - Finance sees requests pending finance approval
    - Stock/Logistique/Maintenance sees FACILITY + FUEL
    - Everyone else sees only their own requests
    """
    roles = _user_roles(current_user)

    if "Admin" in roles:
        return query

    from sqlalchemy import or_

    conditions = []

    # Always allow users to see their own requests
    conditions.append(GenericRequest.requester_id == current_user.id)

    if roles & {"RH"}:
        conditions.append(GenericRequest.type == RequestType.LEAVE)

    if roles & {"Finance"}:
        conditions.append(GenericRequest.type.in_([
            RequestType.FUEL, RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES,
        ]))

    if roles & {"Stock / Logistique", "Maintenance"}:
        conditions.append(GenericRequest.type.in_([
            RequestType.FACILITY_MAINTENANCE,
            RequestType.FACILITY_SUPPLIES,
            RequestType.FUEL,
        ]))

    if roles & {"Direction"}:
        # Direction can view all but not necessarily act
        return query

    return query.filter(or_(*conditions))


# ---------------------------------------------------------------------------
# GET /requests/
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[RequestResponse])
def get_requests(
    type: Optional[RequestType] = None,
    status_filter: Optional[RequestStatus] = Query(None, alias="status"),
    priority: Optional[RequestPriority] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(GenericRequest)

    # Row-level security
    query = _apply_row_level_filter(query, current_user)

    if type:
        query = query.filter(GenericRequest.type == type)
    if status_filter:
        query = query.filter(GenericRequest.status == status_filter)
    if priority:
        query = query.filter(GenericRequest.priority == priority)

    return query.order_by(GenericRequest.created_at.desc()).all()


# ---------------------------------------------------------------------------
# GET /requests/{request_id}
# ---------------------------------------------------------------------------

@router.get("/{request_id}", response_model=RequestResponse)
def get_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Row-level security check: user must own the request or have a qualifying role
    roles = _user_roles(current_user)
    if (
        request.requester_id != current_user.id
        and "Admin" not in roles
        and "Direction" not in roles
        and "RH" not in roles
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this request")

    return request


# ---------------------------------------------------------------------------
# POST /requests/
# ---------------------------------------------------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RequestResponse)
def create_request(
    request_data: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    initial = initial_status_for(request_data.type)

    new_request = GenericRequest(
        type=request_data.type,
        status=initial,
        priority=request_data.priority,
        category=request_data.category,
        requester_id=current_user.id,
        project_id=request_data.project_id,
        description=request_data.description,
        payload=jsonable_encoder(request_data.payload),
        sla_deadline=_compute_sla_deadline(request_data.priority),
    )
    db.add(new_request)
    db.flush()

    # Record creation in audit log
    _record_history(db, new_request, None, initial.value, current_user.id, "Request created")

    db.commit()
    db.refresh(new_request)
    return new_request


# ---------------------------------------------------------------------------
# PATCH /requests/{request_id}/status
# ---------------------------------------------------------------------------

@router.patch("/{request_id}/status", response_model=RequestResponse)
def update_request_status(
    request_id: int,
    payload: RequestUpdateStatus,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    role_names = [r.name.upper() for r in current_user.roles]
    is_admin = "ADMIN" in role_names
    
    if not is_admin:
        if payload.status in {RequestStatus.APPROVED, RequestStatus.REJECTED}:
            if request.type in {RequestType.LEAVE, RequestType.DOCUMENT}:
                if "RH" not in role_names:
                    raise HTTPException(status_code=403, detail="HR approval required")
            elif request.type in {RequestType.IT_EQUIPMENT, RequestType.IT_ACCESS, RequestType.IT_INCIDENT}:
                if "IT" not in role_names:
                    raise HTTPException(status_code=403, detail="IT approval required")
            elif request.type in {RequestType.FACILITY_MAINTENANCE, RequestType.FACILITY_SUPPLIES, RequestType.FACILITY_BADGE, RequestType.FUEL}:
                if "FINANCE" not in role_names and "ACHAT" not in role_names:
                    raise HTTPException(status_code=403, detail="Finance/Achat approval required")

    # Enforce state machine
    if not validate_transition(request.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status transition: {request.status.value} → {payload.status.value}. "
                f"Allowed: {', '.join(s.value for s in __import__('app.modules.requests_unified.services.state_machine', fromlist=['VALID_TRANSITIONS']).VALID_TRANSITIONS.get(request.status, set()))}"
            ),
        )

    old_status = request.status.value
    request.status = payload.status
    request.validator_id = current_user.id

    if payload.rejection_comment:
        request.rejection_comment = payload.rejection_comment

    # Mark resolution timestamp for terminal states
    if payload.status in {RequestStatus.COMPLETED, RequestStatus.REJECTED}:
        request.resolved_at = datetime.utcnow()

    # Record audit history
    _record_history(
        db, request, old_status, payload.status.value,
        current_user.id, payload.rejection_comment,
    )

    db.commit()
    db.refresh(request)

    # --- Post-approval workflows (run asynchronously) ---
    if request.status == RequestStatus.APPROVED and request.type == RequestType.FUEL:
        def _generate_fuel_pdf():
            with SessionLocal() as bg_db:
                try:
                    from app.services.pdf_generator import generate_fuel_request_pdf
                    bg_request = bg_db.get(GenericRequest, request.id)
                    pdf_url = generate_fuel_request_pdf(bg_request, bg_db)
                    bg_request.attachment_url = pdf_url
                    bg_db.commit()
                except Exception:
                    bg_db.rollback()
                    logger.exception("Failed to generate PDF for fuel request %s", request_id)

        background_tasks.add_task(_generate_fuel_pdf)

    if request.status == RequestStatus.APPROVED and request.type == RequestType.LEAVE:
        start_date = request.payload.get("start_date")
        end_date = request.payload.get("end_date")

        if start_date and end_date:
            from datetime import date as date_type
            if isinstance(start_date, str):
                start_date = date_type.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date_type.fromisoformat(end_date)

            target_employee_id = request.payload.get("employee_id") or request.requester_id

            # Use a NEW session for the background task to avoid session lifecycle issues
            def _process_leave():
                with SessionLocal() as bg_db:
                    try:
                        from app.modules.requests_unified.services.leave_workflow import process_approved_leave
                        process_approved_leave(bg_db, int(target_employee_id), start_date, end_date)
                    except Exception:
                        logger.exception("Failed to process approved leave for request %s", request_id)

            background_tasks.add_task(_process_leave)

    if request.status == RequestStatus.APPROVED and request.type in (RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES):
        is_return = request.payload.get("is_return", False)
        if not is_return:
            def _generate_po():
                with SessionLocal() as bg_db:
                    try:
                        from app.models.procurement.purchase import PurchaseOrder, PurchaseOrderLine
                        import uuid
                        po = PurchaseOrder(
                            reference=f"PO-{request_id}-{uuid.uuid4().hex[:6]}".upper(),
                            generic_request_id=request_id,
                            project_id=request.project_id
                        )
                        bg_db.add(po)
                        bg_db.flush()
                        
                        items = request.payload.get("items", [])
                        for item in items:
                            line = PurchaseOrderLine(
                                purchase_order_id=po.id,
                                product_id=item.get("product_id"),
                                designation=item.get("designation", "Article inconnu"),
                                quantity=item.get("quantity", 1),
                                unit_price=0.0
                            )
                            bg_db.add(line)
                        bg_db.commit()
                    except Exception:
                        bg_db.rollback()
                        logger.exception("Failed to process PO for request %s", request_id)
            
            background_tasks.add_task(_generate_po)

    return request


# ---------------------------------------------------------------------------
# DELETE /requests/{request_id}
# ---------------------------------------------------------------------------

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Ownership check: only the requester or an admin can delete
    roles = _user_roles(current_user)
    if request.requester_id != current_user.id and "Admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")

    # Can only delete non-terminal requests
    if request.status in {RequestStatus.COMPLETED, RequestStatus.APPROVED}:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a request that is already approved or completed",
        )

    db.delete(request)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# GET /requests/{request_id}/history
# ---------------------------------------------------------------------------

@router.get("/{request_id}/history")
def get_request_history(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return [
        {
            "id": h.id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "changed_by_id": h.changed_by_id,
            "comment": h.comment,
            "created_at": h.created_at,
        }
        for h in request.history
    ]

# ---------------------------------------------------------------------------
# GET /requests/{request_id}/download-pdf
# ---------------------------------------------------------------------------

@router.get("/{request_id}/download-pdf")
def download_request_pdf(
    request_id: int,
    db: Session = Depends(get_db)
):
    request = db.get(GenericRequest, request_id)
    if not request or not request.attachment_url:
        raise HTTPException(status_code=404, detail="PDF not found")
        
    from fastapi.responses import FileResponse
    import os
    
    file_path = request.attachment_url
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file missing on disk")
        
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"Request_{request_id}.pdf"
    )
