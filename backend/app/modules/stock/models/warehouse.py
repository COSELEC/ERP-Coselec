from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)

from sqlalchemy.orm import relationship

from app.core.database import Base



class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    code = Column(
        String,
        unique=True,
        nullable=False
    )

    name = Column(
        String,
        nullable=False
    )

    address = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    stocks = relationship(
        "Stock",
        back_populates="warehouse"
    )

    stock_movements = relationship(
        "StockMovement",
        back_populates="warehouse"
    )
