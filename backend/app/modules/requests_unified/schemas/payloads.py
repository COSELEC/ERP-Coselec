from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Union, Literal, Annotated
from datetime import date
from typing import Optional, List

class ItemPayload(BaseModel):
    product_id: Optional[int] = None
    designation: str
    quantity: int = Field(gt=0, default=1)
    notes: Optional[str] = None

class LeavePayload(BaseModel):
    type: Literal["LEAVE"] = "LEAVE"
    user_id: Optional[int] = None
    start_date: date
    end_date: date
    leave_type: str = "Congé"
    reason: Optional[str] = None


class ITEquipmentPayload(BaseModel):
    type: Literal["IT_EQUIPMENT"] = "IT_EQUIPMENT"
    is_return: bool = False
    items: List[ItemPayload] = Field(default_factory=list)
    justification: str


class ITAccessPayload(BaseModel):
    type: Literal["IT_ACCESS"] = "IT_ACCESS"
    system_name: str  # e.g. "VPN", "ERP", "Active Directory"
    access_level: str = "standard"  # "standard", "admin"
    justification: str


class ITIncidentPayload(BaseModel):
    type: Literal["IT_INCIDENT"] = "IT_INCIDENT"
    affected_system: str
    error_message: Optional[str] = None
    impact_level: str = "medium"  # "low", "medium", "high", "critical"
    steps_to_reproduce: Optional[str] = None


class FacilityMaintenancePayload(BaseModel):
    type: Literal["FACILITY_MAINTENANCE"] = "FACILITY_MAINTENANCE"
    location: str
    building: Optional[str] = None
    urgency: str = "routine"  # "routine", "urgent", "emergency"
    description: str


class FacilityBadgePayload(BaseModel):
    type: Literal["FACILITY_BADGE"] = "FACILITY_BADGE"
    badge_type: str = "access"  # "access", "parking", "visitor"
    target_user_name: Optional[str] = None
    target_user_id: Optional[int] = None
    zone: Optional[str] = None


class FacilitySuppliesPayload(BaseModel):
    type: Literal["FACILITY_SUPPLIES"] = "FACILITY_SUPPLIES"
    is_return: bool = False
    items: List[ItemPayload] = Field(default_factory=list)
    urgency: str = "routine"
    justification: Optional[str] = None


class FuelPayload(BaseModel):
    type: Literal["FUEL"] = "FUEL"
    user_id: Optional[int] = None
    vehicle_plate: str
    destination: str
    fuel_quantity: float = Field(gt=0)
    trip_days: int = Field(gt=0)
    odometer_reading: int = Field(gt=0)
    trip_purpose: str = ""
    affaire_no: Optional[str] = None
    dossier_no: Optional[str] = None


class DocumentPayload(BaseModel):
    type: Literal["DOCUMENT"] = "DOCUMENT"
    document_type: str  # e.g. "attestation_travail", "fiche_paie", "certificat"
    user_id: Optional[int] = None
    notes: Optional[str] = None


class GenericPayload(BaseModel):
    """Catch-all payload for the OTHER request type."""
    type: Literal["OTHER"] = "OTHER"
    details: Optional[str] = None


# Discriminated union — Pydantic will auto-select the right model based on `payload.type`
RequestPayload = Annotated[
    Union[
        LeavePayload,
        ITEquipmentPayload,
        ITAccessPayload,
        ITIncidentPayload,
        FacilityMaintenancePayload,
        FacilityBadgePayload,
        FacilitySuppliesPayload,
        FuelPayload,
        DocumentPayload,
        GenericPayload,
    ],
    Field(discriminator="type"),
]
