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
from app.models.notification import Notification, NotificationType
from app.core.websockets.manager import broadcast_notification_sync

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


def _notify_creation_targets(db: Session, request: GenericRequest, requester: User) -> None:
    """Notify admins, managers, and relevant role users when a new request is created."""
    try:
        from app.modules.users.models.role import Role
        from app.modules.users.models.user import User

        target_roles = {"Admin"}

        if request.type in {RequestType.LEAVE, RequestType.DOCUMENT}:
            target_roles.update({"RH", "Direction"})
        elif request.type in {RequestType.IT_EQUIPMENT, RequestType.IT_ACCESS, RequestType.IT_INCIDENT}:
            target_roles.update({"IT Admin", "Admin IT", "IT", "Responsable IT"})
        elif request.type in {RequestType.FACILITY_MAINTENANCE, RequestType.FACILITY_SUPPLIES, RequestType.FACILITY_BADGE}:
            target_roles.update({"Facility Manager", "Facility", "Logistique", "Maintenance"})
        elif request.type == RequestType.FUEL:
            target_roles.update({"Finance", "Facility Manager", "Facility", "Direction"})

        recipient_user_ids: set[int] = set()

        # Check direct manager
        requester_emp = db.query(User).filter(User.email == requester.email).first()
        if requester_emp and requester_emp.manager:
            mgr_emp = requester_emp.manager
            mgr_user = db.query(User).filter(User.email == mgr_emp.email).first()
            if mgr_user and mgr_user.id != requester.id:
                recipient_user_ids.add(mgr_user.id)

        # Add users matching target roles
        role_users = db.query(User).filter(User.roles.any(Role.name.in_(target_roles))).all()
        for u in role_users:
            if u.id != requester.id:
                recipient_user_ids.add(u.id)

        msg = f"Nouvelle demande ({request.type.value}) {request.reference} créée par {requester.name}."

        for uid in recipient_user_ids:
            notif = Notification(
                user_id=uid,
                message=msg,
                type=NotificationType.INFO.value,
                reference_id=request.id
            )
            db.add(notif)
            db.flush()
            try:
                broadcast_notification_sync(uid, {
                    "event_type": "NEW_NOTIFICATION",
                    "data": {
                        "id": notif.id,
                        "message": msg,
                        "type": "info",
                        "is_read": False,
                        "reference_id": request.id,
                        "created_at": notif.created_at.isoformat()
                    }
                })
            except Exception as e:
                logger.error(f"Failed to broadcast request creation notification to user {uid}: {e}")
    except Exception as err:
        logger.error(f"Error in _notify_creation_targets: {err}")


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

    if roles & {"IT Admin", "Admin IT", "IT", "Responsable IT"}:
        conditions.append(GenericRequest.type.in_([
            RequestType.IT_EQUIPMENT,
            RequestType.IT_ACCESS,
            RequestType.IT_INCIDENT,
        ]))

    if roles & {"Finance"}:
        conditions.append(GenericRequest.type.in_([
            RequestType.FUEL, RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES,
        ]))

    if roles & {"Stock / Logistique", "Maintenance", "Facility Manager", "Facility"}:
        conditions.append(GenericRequest.type.in_([
            RequestType.FACILITY_MAINTENANCE,
            RequestType.FACILITY_SUPPLIES,
            RequestType.FACILITY_BADGE,
            RequestType.FUEL,
        ]))

    if roles & {"Direction"}:
        # Direction can view all but not necessarily act
        return query

    return query.filter(or_(*conditions))


# ---------------------------------------------------------------------------
# GET /requests/
# ---------------------------------------------------------------------------

@router.get("", response_model=list[RequestResponse])
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

@router.post("", status_code=status.HTTP_201_CREATED, response_model=RequestResponse)
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

    # Immediate Budget Impact
    if new_request.project_id and new_request.type in (RequestType.FUEL, RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES):
        from app.models.project.expense import ProjectExpense
        from app.models.project.budget import ProjectBudget
        
        estimated_amount = 0.0
        if new_request.type == RequestType.FUEL:
            # Prix fixe pour le carburant: 1000 XOF le litre (ou selon la logique métier)
            qty = float(new_request.payload.get("quantity_liters") or new_request.payload.get("quantity") or 0)
            estimated_amount = qty * 1000.0
        else:
            # Pour le matériel, s'il y a un estimated_cost dans le payload
            estimated_amount = float(new_request.payload.get("estimated_cost") or 0.0)
            
        if estimated_amount > 0:
            # Trouver le budget approprié pour le projet (ex: le premier budget de la catégorie correspondante, ou le budget global)
            budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == new_request.project_id).first()
            if budget:
                expense = ProjectExpense(
                    project_id=new_request.project_id,
                    budget_id=budget.id,
                    expense_date=datetime.utcnow().date(),
                    amount=estimated_amount,
                    currency=budget.currency or "XOF",
                    category="Achat/Carburant" if new_request.type == RequestType.FUEL else "Achat Matériel",
                    description=f"Demande {new_request.type.value} #{new_request.id}",
                    status="PENDING", # PENDING means it's an engagement, not yet paid
                    reference=f"REQ-{new_request.id}",
                )
                db.add(expense)
                db.flush()

    # Record creation in audit log
    _record_history(db, new_request, None, initial.value, current_user.id, "Request created")

    # Notify managers and target administrators
    _notify_creation_targets(db, new_request, current_user)

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

    role_names = {r.name.upper() for r in current_user.roles}
    is_admin = "ADMIN" in role_names
    
    if not is_admin:
        if payload.status == RequestStatus.PENDING_FINANCE_APPROVAL or (payload.status == RequestStatus.REJECTED and request.status == RequestStatus.PENDING_MANAGER_APPROVAL):
            if "DIRECTION" not in role_names:
                from app.modules.users.models.user import User
                current_employee = db.query(User).filter(User.email == current_user.email).first()
                requester = db.get(User, request.requester_id)
                requester_employee = db.query(User).filter(User.email == requester.email).first() if requester else None
                
                is_direct_manager = current_employee and requester_employee and requester_employee.manager_id == current_employee.id
                if not is_direct_manager:
                    raise HTTPException(status_code=403, detail="Manager or Direction approval required")
                    
        elif payload.status in {RequestStatus.APPROVED, RequestStatus.REJECTED}:
            if request.type in {RequestType.LEAVE, RequestType.DOCUMENT}:
                if not (role_names & {"RH", "HR", "DIRECTION"} or any("RH" in r for r in role_names)):
                    raise HTTPException(status_code=403, detail="HR approval required")
            elif request.type in {RequestType.IT_EQUIPMENT, RequestType.IT_ACCESS, RequestType.IT_INCIDENT}:
                it_roles = {"IT", "IT ADMIN", "ADMIN IT", "RESPONSABLE IT"}
                if not (role_names & it_roles or any("IT" in r for r in role_names)):
                    raise HTTPException(status_code=403, detail="IT approval required")
            elif request.type in {RequestType.FACILITY_MAINTENANCE, RequestType.FACILITY_SUPPLIES, RequestType.FACILITY_BADGE, RequestType.FUEL}:
                facility_roles = {"FINANCE", "ACHAT", "FINANCE / BUDGET", "FACILITY", "FACILITY MANAGER", "LOGISTIQUE", "STOCK / LOGISTIQUE", "MAINTENANCE"}
                if not (role_names & facility_roles or any(term in r for r in role_names for term in ["FACILITY", "FINANCE", "ACHAT"])):
                    raise HTTPException(status_code=403, detail="Finance/Achat/Facility approval required")

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
    
    if payload.status == RequestStatus.PENDING_FINANCE_APPROVAL:
        request.manager_validator_id = current_user.id
        request.manager_validated_at = datetime.utcnow()
    elif payload.status == RequestStatus.APPROVED and old_status == RequestStatus.PENDING_FINANCE_APPROVAL:
        request.finance_validator_id = current_user.id
        request.finance_validated_at = datetime.utcnow()

    if payload.rejection_comment:
        request.rejection_comment = payload.rejection_comment

    # Cancel Budget Impact if Rejected/Cancelled
    if payload.status in {RequestStatus.REJECTED, RequestStatus.CANCELLED}:
        from app.models.project.expense import ProjectExpense
        expense = db.query(ProjectExpense).filter(ProjectExpense.reference == f"REQ-{request.id}").first()
        if expense:
            db.delete(expense)

    # Mark resolution timestamp for terminal states
    if payload.status in {RequestStatus.COMPLETED, RequestStatus.REJECTED}:
        request.resolved_at = datetime.utcnow()

    # Record audit history
    _record_history(
        db, request, old_status, payload.status.value,
        current_user.id, payload.rejection_comment,
    )
    
    # Notify user on approval or rejection
    if payload.status in {RequestStatus.APPROVED, RequestStatus.REJECTED}:
        if payload.status == RequestStatus.REJECTED:
            reason_str = f" (Motif : {payload.rejection_comment})" if payload.rejection_comment else ""
            msg = f"Votre demande {request.reference} a été rejetée.{reason_str}"
        else:
            msg = f"Votre demande {request.reference} a été approuvée."

        new_notification = Notification(
            user_id=request.requester_id,
            message=msg,
            type=NotificationType.INFO.value,
            reference_id=request.id
        )
        db.add(new_notification)
        db.flush()
        
        # Broadcast via WebSockets
        try:
            broadcast_notification_sync(request.requester_id, {
                "event_type": "NEW_NOTIFICATION",
                "data": {
                    "id": new_notification.id,
                    "message": msg,
                    "type": "info",
                    "is_read": False,
                    "reference_id": request.id,
                    "created_at": new_notification.created_at.isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast notification: {e}")

    db.commit()
    db.refresh(request)

    # --- Post-approval workflows (run asynchronously) ---
    if request.status == RequestStatus.APPROVED and request.type == RequestType.FUEL:
        def _generate_fuel_pdf():
            with SessionLocal() as bg_db:
                try:
                    from app.services.pdf_generator import generate_dmcar_pdf
                    bg_request = bg_db.get(GenericRequest, request.id)
                    pdf_url = generate_dmcar_pdf(bg_request)
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

            target_user_id = request.payload.get("user_id") or request.requester_id

            # Use a NEW session for the background task to avoid session lifecycle issues
            def _process_leave():
                with SessionLocal() as bg_db:
                    try:
                        from app.modules.requests_unified.services.leave_workflow import process_approved_leave
                        process_approved_leave(bg_db, int(target_user_id), start_date, end_date)
                    except Exception:
                        logger.exception("Failed to process approved leave for request %s", request_id)

            background_tasks.add_task(_process_leave)

    if request.status == RequestStatus.APPROVED and request.type in (RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES, RequestType.FUEL):
        is_return = request.payload.get("is_return", False)
        if not is_return:
            def _generate_caisse_voucher():
                with SessionLocal() as bg_db:
                    try:
                        from app.models.caisse_voucher import CaisseVoucher, CaisseVoucherStatus
                        from app.models.project.expense import ProjectExpense
                        
                        expense = bg_db.query(ProjectExpense).filter(ProjectExpense.reference == f"REQ-{request_id}").first()
                        amount = expense.amount if expense else 0.0
                        
                        voucher = CaisseVoucher(
                            date=datetime.utcnow(),
                            description=f"Demande de décaissement pour {request.type.value} #{request_id}",
                            type="Sortie",
                            amount=amount,
                            beneficiary=request.payload.get("beneficiary", "Fournisseur inconnu"),
                            status=CaisseVoucherStatus.DRAFT,
                            generic_request_id=request_id
                        )
                        bg_db.add(voucher)
                        bg_db.commit()
                    except Exception:
                        bg_db.rollback()
                        logger.exception("Failed to generate Caisse Voucher for request %s", request_id)
            
            background_tasks.add_task(_generate_caisse_voucher)

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
        
    from fastapi.responses import RedirectResponse
    from app.services.storage import get_file_url_from_minio
    
    file_path = request.attachment_url
    
    try:
        url = get_file_url_from_minio(file_path)
        return RedirectResponse(url=url)
    except Exception as e:
        logger.error(f"Error generating presigned URL for {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving PDF from storage")
