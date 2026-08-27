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
            target_roles.update({"RH", "RH / Comptabilité", "Direction"})
        elif request.type in {RequestType.IT_EQUIPMENT, RequestType.IT_ACCESS, RequestType.IT_INCIDENT}:
            target_roles.update({"IT Admin", "Admin IT", "IT", "Responsable IT"})
        elif request.type in {RequestType.FACILITY_MAINTENANCE, RequestType.FACILITY_SUPPLIES, RequestType.FACILITY_BADGE}:
            target_roles.update({"Facility Manager", "Facility", "Logistique", "Maintenance"})
        elif request.type == RequestType.FUEL:
            target_roles.update({"Finance", "Facility Manager", "Facility", "Direction"})

        recipient_user_ids: set[int] = set()

        requester_emp = db.query(User).filter(User.email == requester.email).first()
        if requester_emp and requester_emp.manager:
            mgr_emp = requester_emp.manager
            mgr_user = db.query(User).filter(User.email == mgr_emp.email).first()
            if mgr_user and mgr_user.id != requester.id:
                recipient_user_ids.add(mgr_user.id)

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

    conditions.append(GenericRequest.requester_id == current_user.id)

    if roles & {"RH", "RH / Comptabilité"}:
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
        return query

    return query.filter(or_(*conditions))



@router.get("", response_model=list[RequestResponse])
def get_requests(
    type: Optional[RequestType] = None,
    status_filter: Optional[RequestStatus] = Query(None, alias="status"),
    priority: Optional[RequestPriority] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(GenericRequest)

    query = _apply_row_level_filter(query, current_user)

    if type:
        query = query.filter(GenericRequest.type == type)
    if status_filter:
        query = query.filter(GenericRequest.status == status_filter)
    if priority:
        query = query.filter(GenericRequest.priority == priority)

    return query.order_by(GenericRequest.created_at.desc()).all()



@router.get("/{request_id}", response_model=RequestResponse)
def get_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Requête introuvable")

    roles = _user_roles(current_user)
    if (
        request.requester_id != current_user.id
        and "Admin" not in roles
        and "Direction" not in roles
        and "RH" not in roles
        and "RH / Comptabilité" not in roles
    ):
        raise HTTPException(status_code=403, detail="Non autorisé à consulter cette requête")

    return request



@router.post("", status_code=status.HTTP_201_CREATED, response_model=RequestResponse)
def create_request(
    request_data: RequestCreate,
    background_tasks: BackgroundTasks,
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

    if new_request.project_id and new_request.type in (RequestType.FUEL, RequestType.IT_EQUIPMENT, RequestType.FACILITY_SUPPLIES):
        from app.models.project.expense import ProjectExpense
        from app.models.project.budget import ProjectBudget
        
        estimated_amount = 0.0
        if new_request.type == RequestType.FUEL:
            qty = float(new_request.payload.get("quantity_liters") or new_request.payload.get("quantity") or 0)
            estimated_amount = qty * 1000.0
        else:
            estimated_amount = float(new_request.payload.get("estimated_cost") or 0.0)
            
        if estimated_amount > 0:
            budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == new_request.project_id).first()
            if budget:
                expense = ProjectExpense(
                    project_id=new_request.project_id,
                    budget_id=budget.id,
                    date_incurred=datetime.utcnow().date(),
                    amount=estimated_amount,
                    description=f"REQ-{new_request.id} : Demande {new_request.type.value}",
                    status="PENDING", 
                )
                db.add(expense)
                db.flush()

    _record_history(db, new_request, None, initial.value, current_user.id, "Request created")

    _notify_creation_targets(db, new_request, current_user)

    db.commit()
    db.refresh(new_request)
    
    if new_request.type == RequestType.FUEL:
        def _generate_initial_fuel_pdf(req_id: int):
            with SessionLocal() as bg_db:
                try:
                    from app.services.pdf_generator import generate_dmcar_pdf
                    bg_request = bg_db.get(GenericRequest, req_id)
                    if bg_request:
                        pdf_url = generate_dmcar_pdf(bg_request)
                        bg_request.attachment_url = pdf_url
                        bg_db.commit()
                except Exception:
                    bg_db.rollback()
                    
        background_tasks.add_task(_generate_initial_fuel_pdf, new_request.id)
        
    return new_request



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
        raise HTTPException(status_code=404, detail="Requête introuvable")

    role_names = {r.name.upper() for r in current_user.roles}
    is_admin = "ADMIN" in role_names
    
    if not is_admin:
        if payload.status == RequestStatus.PENDING_FINANCE_APPROVAL or (payload.status == RequestStatus.REJECTED and request.status == RequestStatus.PENDING_MANAGER_APPROVAL) or (request.status == RequestStatus.COMPROMISE_PENDING and payload.status in {RequestStatus.APPROVED, RequestStatus.REJECTED}):
            if "DIRECTION" not in role_names:
                requester = db.get(User, request.requester_id)
                
                is_direct_manager = requester and requester.manager_id == current_user.id
                if not is_direct_manager:
                    raise HTTPException(status_code=403, detail="Approbation du responsable ou de la direction requise")
                    
        elif payload.status in {RequestStatus.APPROVED, RequestStatus.REJECTED} and request.status != RequestStatus.COMPROMISE_PENDING:
            if request.type in {RequestType.LEAVE, RequestType.DOCUMENT}:
                if not (role_names & {"RH", "HR", "DIRECTION"} or any("RH" in r for r in role_names)):
                    raise HTTPException(status_code=403, detail="Approbation RH requise")
            elif request.type in {RequestType.IT_EQUIPMENT, RequestType.IT_ACCESS, RequestType.IT_INCIDENT}:
                it_roles = {"IT", "IT ADMIN", "ADMIN IT", "RESPONSABLE IT"}
                if not (role_names & it_roles or any("IT" in r for r in role_names)):
                    raise HTTPException(status_code=403, detail="Approbation IT requise")
            elif request.type in {RequestType.FACILITY_MAINTENANCE, RequestType.FACILITY_SUPPLIES, RequestType.FACILITY_BADGE, RequestType.FUEL}:
                facility_roles = {"FINANCE", "ACHAT", "FINANCE / BUDGET", "FACILITY", "FACILITY MANAGER", "LOGISTIQUE", "STOCK / LOGISTIQUE", "MAINTENANCE"}
                if not (role_names & facility_roles or any(term in r for r in role_names for term in ["FACILITY", "FINANCE", "ACHAT"])):
                    raise HTTPException(status_code=403, detail="Approbation Finance/Achat/Services Généraux requise")

    if not validate_transition(request.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status transition: {request.status.value} → {payload.status.value}. "
                f"Allowed: {', '.join(s.value for s in __import__('app.modules.requests_unified.services.state_machine', fromlist=['VALID_TRANSITIONS']).VALID_TRANSITIONS.get(request.status, set()))}"
            ),
        )

    old_status = request.status.value

    # Handle payload updates and fuel compromise
    is_finance_compromise = False
    if payload.updated_payload:
        if request.type == RequestType.FUEL:
            old_quantity = request.payload.get("fuel_quantity")
            new_quantity = payload.updated_payload.get("fuel_quantity")
            if old_quantity and new_quantity and float(new_quantity) < float(old_quantity):
                payload.updated_payload["original_fuel_quantity"] = float(old_quantity)
                # Force status to compromise pending if finance is approving
                if payload.status == RequestStatus.APPROVED and request.status == RequestStatus.PENDING_FINANCE_APPROVAL:
                    payload.status = RequestStatus.COMPROMISE_PENDING
                    is_finance_compromise = True
        
        # Merge updated payload
        request.payload = {**request.payload, **payload.updated_payload}
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(request, "payload")

    request.status = payload.status
    request.validator_id = current_user.id
    
    if payload.status == RequestStatus.PENDING_FINANCE_APPROVAL:
        request.manager_validator_id = current_user.id
        request.manager_validated_at = datetime.utcnow()
    elif (payload.status == RequestStatus.APPROVED or is_finance_compromise) and old_status == RequestStatus.PENDING_FINANCE_APPROVAL:
        request.finance_validator_id = current_user.id
        request.finance_validated_at = datetime.utcnow()

    if payload.rejection_comment:
        request.rejection_comment = payload.rejection_comment

    if payload.status == RequestStatus.REJECTED:
        from app.models.project.expense import ProjectExpense
        expense = db.query(ProjectExpense).filter(ProjectExpense.description.like(f"REQ-{request.id} :%")).first()
        if expense:
            db.delete(expense)

    if payload.status in {RequestStatus.COMPLETED, RequestStatus.REJECTED}:
        request.resolved_at = datetime.utcnow()

    _record_history(
        db, request, old_status, payload.status.value,
        current_user.id, payload.rejection_comment,
    )
    
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

    if request.type == RequestType.FUEL:
        def _generate_fuel_pdf(req_id: int):
            with SessionLocal() as bg_db:
                try:
                    from app.services.pdf_generator import generate_dmcar_pdf
                    bg_request = bg_db.get(GenericRequest, req_id)
                    if bg_request:
                        pdf_url = generate_dmcar_pdf(bg_request)
                        bg_request.attachment_url = pdf_url
                        bg_db.commit()
                except Exception:
                    bg_db.rollback()

        background_tasks.add_task(_generate_fuel_pdf, request.id)

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
                        from app.models.caisse_voucher import CaisseVoucher, VoucherStatus, CaisseVoucherLine, CaisseVoucherLineType
                        # ProjectExpense no longer has a 'reference' column. Setting amount to 0 for now
                        amount = 0.0
                        
                        voucher = CaisseVoucher(
                            num=f"REQ-{request_id}",
                            expense_id=None,
                            status=VoucherStatus.DRAFT
                        )
                        bg_db.add(voucher)
                        bg_db.flush()
                        
                        line = CaisseVoucherLine(
                            voucher_id=voucher.id,
                            line_type=CaisseVoucherLineType.EXPENSE,
                            date=datetime.utcnow().strftime("%d/%m/%Y"),
                            designation=f"Décaissement {request.type.value} #{request_id}",
                            amount=amount
                        )
                        bg_db.add(line)
                        bg_db.commit()
                    except Exception:
                        bg_db.rollback()
                        logger.exception("Failed to generate Caisse Voucher for request %s", request_id)
            
            background_tasks.add_task(_generate_caisse_voucher)

    return request



@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Requête introuvable")

    roles = _user_roles(current_user)
    if request.requester_id != current_user.id and "Admin" not in roles:
        raise HTTPException(status_code=403, detail="Non autorisé à supprimer cette requête")

    if request.status in {RequestStatus.COMPLETED, RequestStatus.APPROVED}:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a request that is already approved or completed",
        )

    db.delete(request)
    db.commit()
    return None



@router.get("/{request_id}/history")
def get_request_history(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(GenericRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Requête introuvable")

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


@router.get("/{request_id}/download-pdf")
def download_request_pdf(
    request_id: int,
    db: Session = Depends(get_db)
):
    request = db.get(GenericRequest, request_id)
    if not request or not request.attachment_url:
        raise HTTPException(status_code=404, detail="PDF introuvable")
        
    from fastapi.responses import RedirectResponse
    from app.services.storage import get_file_url_from_minio
    
    file_path = request.attachment_url
    
    try:
        url = get_file_url_from_minio(file_path)
        return RedirectResponse(url=url)
    except Exception as e:
        logger.error(f"Error generating presigned URL for {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du PDF")
