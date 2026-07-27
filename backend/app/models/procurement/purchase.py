import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class PurchaseRequestStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "Draft"
    ISSUED = "Issued"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requester_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(SQLEnum(PurchaseRequestStatus), default=PurchaseRequestStatus.PENDING)
    description = Column(Text, nullable=True)
    expected_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    requester = relationship("Employee")
    orders = relationship("PurchaseOrder", back_populates="purchase_request", cascade="all, delete-orphan")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(100), unique=True, index=True, nullable=True)
    purchase_request_id = Column(Integer, ForeignKey("purchase_requests.id", ondelete="SET NULL"), nullable=True)
    generic_request_id = Column(Integer, ForeignKey("requests.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)
    total_amount = Column(Numeric(14, 2), default=0.0)
    pdf_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    purchase_request = relationship("PurchaseRequest", back_populates="orders")
    supplier = relationship("Partner")
    lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    designation = Column(String(255), nullable=True)
    
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(14, 2), nullable=False, default=0.0)

    order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")
