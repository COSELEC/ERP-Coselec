import enum
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class StockType(str, enum.Enum):
    GENERAL = "GENERAL"
    PROJECT = "PROJECT"


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
        nullable=True  # nullable pour stocks sans partenaire associé
    )

    stock_type = Column(
        SQLEnum(StockType),
        default=StockType.GENERAL,
        nullable=False
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True
    )

    quantity = Column(
        Integer,
        default=0
    )
    
    warehouse = relationship(
        "Warehouse",
        back_populates="stocks"
    )
    project = relationship("Project")
