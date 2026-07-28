from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

from app.modules.stock.enums.movement_type import MovementType


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False
    )

    partner_id = Column(
        Integer,
        ForeignKey("partners.id"),
        nullable=False
    )

    type = Column(
        Enum(MovementType),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True
    )

    product = relationship("Product")
    warehouse = relationship("Warehouse", back_populates="stock_movements")
    partner = relationship("Partner")
    project = relationship("Project")
