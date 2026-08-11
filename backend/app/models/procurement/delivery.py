from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class DeliveryNote(Base):
    __tablename__ = "delivery_notes"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    supplier_name = Column(String, nullable=True)
    supplier_reference = Column(String, nullable=True) 
    
    delivery_date = Column(DateTime, default=datetime.utcnow)
    
    storekeeper_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    storekeeper_validated_at = Column(DateTime, nullable=True)
    
    project_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_manager_validated_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    purchase_order = relationship("PurchaseOrder", back_populates="delivery_notes")
    storekeeper = relationship("User", foreign_keys=[storekeeper_id])
    project_manager = relationship("User", foreign_keys=[project_manager_id])
    lines = relationship("DeliveryNoteLine", back_populates="delivery_note", cascade="all, delete-orphan")


class DeliveryNoteLine(Base):
    __tablename__ = "delivery_note_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_note_id = Column(Integer, ForeignKey("delivery_notes.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    designation = Column(String, nullable=False)
    ordered_quantity = Column(Float, default=0.0)
    delivered_quantity = Column(Float, default=0.0)
    is_compliant = Column(Boolean, default=True)
    remarks = Column(Text, nullable=True)
    
    delivery_note = relationship("DeliveryNote", back_populates="lines")
    product = relationship("Product")
