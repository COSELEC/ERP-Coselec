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

    # Geographic location — one row = one partner × one localité
    region      = Column(String(100), nullable=True)
    departement = Column(String(100), nullable=True)
    commune     = Column(String(100), nullable=True)
    localite    = Column(String(200), nullable=True)

    project = relationship("Project")
    partner = relationship("Partner")
