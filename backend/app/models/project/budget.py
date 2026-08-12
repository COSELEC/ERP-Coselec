import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ProjectBudget(Base):
    __tablename__ = "project_budgets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    
    category = Column(String(100), nullable=False)
    allocated_amount = Column(Numeric(14, 2), default=0.0)
    currency = Column(String(10), default="XOF")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="budgets")
    partner = relationship("Partner")
    expenses = relationship("ProjectExpense", back_populates="budget", cascade="all, delete-orphan")

    @property
    def consumed(self) -> float:
        return sum(e.amount for e in self.expenses if getattr(e.status, 'value', e.status) == "Approved")

    @property
    def remaining_amount(self) -> float:
        return self.allocated_amount - self.consumed
