import enum
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ReservationStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    CONSUMED = "Consumed"
    CANCELLED = "Cancelled"

class ProjectStockReservation(Base):
    __tablename__ = "project_stock_reservations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    reserved_by_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    consumed_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    product = relationship("Product")
    reserved_by = relationship("Employee")
