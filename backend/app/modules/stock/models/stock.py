from sqlalchemy import (
    Column,
    Integer,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

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

    quantity = Column(
        Integer,
        default=0
    )
    warehouse = relationship(
        "Warehouse",
        back_populates="stocks"
    )
