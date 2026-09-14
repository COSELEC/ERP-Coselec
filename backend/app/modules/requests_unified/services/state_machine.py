"""
State Machine Engine for the unified request workflow.

Enforces valid status transitions and determines routing
based on request type (e.g., which types require finance approval).
"""

from __future__ import annotations

from app.modules.requests_unified.models.request import RequestStatus, RequestType


VALID_TRANSITIONS: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.DRAFT:            {RequestStatus.PENDING},
    RequestStatus.PENDING:          {RequestStatus.APPROVED, RequestStatus.REJECTED},
    RequestStatus.PENDING_MANAGER_APPROVAL: {RequestStatus.PENDING_FINANCE_APPROVAL, RequestStatus.PENDING_DGA_APPROVAL, RequestStatus.REJECTED, RequestStatus.COMPROMISE_PENDING},
    RequestStatus.PENDING_DGA_APPROVAL: {RequestStatus.PENDING_DG_APPROVAL, RequestStatus.REJECTED},
    RequestStatus.PENDING_DG_APPROVAL: {RequestStatus.APPROVED, RequestStatus.REJECTED},
    RequestStatus.COMPROMISE_PENDING: {RequestStatus.PENDING_FINANCE_APPROVAL, RequestStatus.APPROVED, RequestStatus.REJECTED},
    RequestStatus.PENDING_FINANCE_APPROVAL: {RequestStatus.APPROVED, RequestStatus.REJECTED},
    RequestStatus.APPROVED:         {RequestStatus.IN_PROGRESS, RequestStatus.COMPLETED},
    RequestStatus.IN_PROGRESS:      {RequestStatus.ON_HOLD, RequestStatus.COMPLETED},
    RequestStatus.ON_HOLD:          {RequestStatus.IN_PROGRESS, RequestStatus.REJECTED},
    RequestStatus.COMPLETED:        set(),   
    RequestStatus.REJECTED:         set(),   
}


def validate_transition(current: RequestStatus, target: RequestStatus) -> bool:
    """Return True when *target* is a valid successor of *current*."""
    return target in VALID_TRANSITIONS.get(current, set())


REQUIRES_MANAGER_APPROVAL: set[RequestType] = {
    RequestType.LEAVE,
    RequestType.IT_EQUIPMENT,
    RequestType.FACILITY_SUPPLIES,
}

REQUIRES_FINANCE_APPROVAL: set[RequestType] = {
    RequestType.IT_EQUIPMENT,
    RequestType.FUEL,
    RequestType.FACILITY_SUPPLIES,
}

REQUIRES_DGA_APPROVAL: set[RequestType] = {
    RequestType.PIECE_CAISSE,
}

REQUIRES_DG_APPROVAL: set[RequestType] = {
    RequestType.PIECE_CAISSE,
}


def initial_status_for(request_type: RequestType) -> RequestStatus:
    """
    Determine the initial status a newly created request should land on.
    """
    if request_type in {RequestType.FUEL, RequestType.PIECE_CAISSE}:
        return RequestStatus.PENDING_MANAGER_APPROVAL
    return RequestStatus.PENDING


SLA_HOURS: dict[str, int] = {
    "LOW":    168,   
    "NORMAL": 72,    
    "HIGH":   24,    
    "URGENT": 4,     
}
