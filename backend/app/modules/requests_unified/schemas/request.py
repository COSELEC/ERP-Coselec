from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Union, Literal, Annotated
from datetime import date, datetime
from typing import Optional

from app.modules.requests_unified.models.request import (
    RequestType,
    RequestStatus,
    RequestPriority,
)


from app.modules.requests_unified.schemas.payloads import RequestPayload

# ---------------------------------------------------------------------------
# Request CRUD schemas
# ---------------------------------------------------------------------------


class RequestBase(BaseModel):
    description: Optional[str] = None
    project_id: Optional[int] = None


class RequestCreate(RequestBase):
    type: RequestType
    priority: RequestPriority = RequestPriority.NORMAL
    category: Optional[str] = None
    payload: RequestPayload


class RequestUpdateStatus(BaseModel):
    status: RequestStatus
    rejection_comment: Optional[str] = None


class RequestHistoryResponse(BaseModel):
    id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_id: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RequestResponse(RequestBase):
    id: int
    reference: str
    type: RequestType
    status: RequestStatus
    priority: RequestPriority
    category: Optional[str] = None
    requester_id: int
    validator_id: Optional[int] = None
    department_id: Optional[int] = None
    rejection_comment: Optional[str] = None
    payload: dict  # Return as raw dict so any payload type works
    attachment_url: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    manager_validator_id: Optional[int] = None
    manager_validated_at: Optional[datetime] = None
    finance_validator_id: Optional[int] = None
    finance_validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    history: list[RequestHistoryResponse] = []

    class Config:
        from_attributes = True
