import enum
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class VoucherStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"
    VOID = "VOID"

class CaisseVoucherLineType(str, enum.Enum):
    EXPENSE = "EXPENSE"
    RECEIPT = "RECEIPT"

class CaisseVoucher(Base):
    __tablename__ = "caisse_vouchers"
    
    id = Column(Integer, primary_key=True, index=True)
    num = Column(String(50), nullable=True)
    affaire = Column(String(255), nullable=True)
    cia = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=True)
    
    status = Column(SQLEnum(VoucherStatus), default=VoucherStatus.DRAFT)
    finalized_at = Column(DateTime, nullable=True)
    
    pdf_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    expense_id = Column(Integer, ForeignKey("project_expenses.id", ondelete="SET NULL"), nullable=True)
    reservation_id = Column(Integer, ForeignKey("project_stock_reservations.id", ondelete="SET NULL"), nullable=True)

    demandeur_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validator_cg_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validator_dga_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validator_dg_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    project = relationship("Project")
    expense = relationship("ProjectExpense")
    reservation = relationship("ProjectStockReservation")
    
    demandeur = relationship("User", foreign_keys=[demandeur_id])
    validator_cg = relationship("User", foreign_keys=[validator_cg_id])
    validator_dga = relationship("User", foreign_keys=[validator_dga_id])
    validator_dg = relationship("User", foreign_keys=[validator_dg_id])
    
    lines = relationship("CaisseVoucherLine", back_populates="voucher", cascade="all, delete-orphan")
    attachments = relationship("VoucherAttachment", cascade="all, delete-orphan")

class CaisseVoucherLine(Base):
    __tablename__ = "caisse_voucher_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("caisse_vouchers.id", ondelete="CASCADE"), nullable=False)
    line_type = Column(SQLEnum(CaisseVoucherLineType), nullable=False)
    
    date = Column(String(50), nullable=True)
    designation = Column(String(255), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    
    voucher = relationship("CaisseVoucher", back_populates="lines")
