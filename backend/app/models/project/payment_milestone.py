import enum
from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base

class PaymentMilestoneStatus(str, enum.Enum):
    PENDING = "Pending"
    INVOICED = "Invoiced"
    PAID = "Paid"

class PaymentMilestone(Base):
    __tablename__ = "project_payment_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(SQLEnum(PaymentMilestoneStatus), default=PaymentMilestoneStatus.PENDING)

    project = relationship("Project")
    partner = relationship("Partner")
