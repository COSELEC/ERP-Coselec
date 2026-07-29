import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ExpenseStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    budget_id = Column(Integer, ForeignKey("project_budgets.id", ondelete="SET NULL"), nullable=True)
    purchase_order_line_id = Column(Integer, ForeignKey("purchase_order_lines.id", ondelete="SET NULL"), nullable=True)
    
    amount = Column(Numeric(14, 2), nullable=False)
    date_incurred = Column(Date, nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(SQLEnum(ExpenseStatus), default=ExpenseStatus.PENDING)
    proof_document_url = Column(String(500), nullable=True)

    project = relationship("Project", back_populates="expenses")
    budget = relationship("ProjectBudget", back_populates="expenses")
    purchase_order_line = relationship("PurchaseOrderLine")
