import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class RequestType(str, enum.Enum):
    LEAVE = "LEAVE"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    IT_ACCESS = "IT_ACCESS"
    IT_INCIDENT = "IT_INCIDENT"
    FACILITY_MAINTENANCE = "FACILITY_MAINTENANCE"
    FACILITY_BADGE = "FACILITY_BADGE"
    FACILITY_SUPPLIES = "FACILITY_SUPPLIES"
    FUEL = "FUEL"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"


class RequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class RequestPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class GenericRequest(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    
    @property
    def reference(self) -> str:
        return f"DEM-{self.id:04d}" if self.id else "DEM-XXXX"

    type = Column(SQLEnum(RequestType), nullable=False)
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    priority = Column(SQLEnum(RequestPriority), default=RequestPriority.NORMAL)

    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    validator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    description = Column(String, nullable=True)
    category = Column(String, nullable=True)  # Sub-category (e.g., "Laptop", "VPN Access")
    rejection_comment = Column(String, nullable=True)

    # Payload JSON — stores type-specific fields
    # e.g. {"start_date": "2026-07-21", "end_date": "2026-07-25"} for LEAVE
    # e.g. {"equipment_type": "laptop", "specifications": "16GB RAM"} for IT_EQUIPMENT
    payload = Column(JSON, default=dict)

    attachment_url = Column(String, nullable=True)

    # SLA Tracking
    sla_deadline = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Multi-step Approval
    manager_validator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager_validated_at = Column(DateTime, nullable=True)
    finance_validator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    finance_validated_at = Column(DateTime, nullable=True)

    # Asset/Stock Linkage
    linked_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    linked_purchase_request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    validator = relationship("User", foreign_keys=[validator_id])
    manager_validator = relationship("User", foreign_keys=[manager_validator_id])
    finance_validator = relationship("User", foreign_keys=[finance_validator_id])
    project = relationship("Project", foreign_keys=[project_id])
    department = relationship("Department", foreign_keys=[department_id])
    linked_product = relationship("Product", foreign_keys=[linked_product_id])
    history = relationship("RequestHistory", back_populates="request", cascade="all, delete-orphan",
                           order_by="RequestHistory.created_at.desc()")


class RequestHistory(Base):
    """Immutable audit log tracking every state change on a request."""
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    request = relationship("GenericRequest", back_populates="history")
    changed_by = relationship("User", foreign_keys=[changed_by_id])
