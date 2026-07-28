from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base

class ReceptionControl(Base):
    __tablename__ = "reception_controls"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    
    delivery_date = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    pdf_url = Column(String, nullable=True)
    
    lines = relationship("ReceptionControlLine", back_populates="reception_control", cascade="all, delete-orphan")

class ReceptionControlLine(Base):
    __tablename__ = "reception_control_lines"

    id = Column(Integer, primary_key=True, index=True)
    reception_id = Column(Integer, ForeignKey("reception_controls.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    designation = Column(String, nullable=False)
    
    qty_ordered = Column(Integer, default=0)
    qty_delivered = Column(Integer, default=0)
    is_compliant = Column(Boolean, default=True)
    notes = Column(String, nullable=True)
    
    reception_control = relationship("ReceptionControl", back_populates="lines")
