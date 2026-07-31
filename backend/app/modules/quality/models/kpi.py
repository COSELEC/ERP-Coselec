from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from app.core.database.session import Base

class KPIOperator(str, enum.Enum):
    GTE = "GTE"        # >=
    LTE = "LTE"        # <=
    BETWEEN = "BETWEEN"
    EQ = "EQ"          # ==

class KPIProcessus(Base):
    __tablename__ = "quality_kpi_processus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)

    indicators = relationship("KPIIndicator", back_populates="processus", cascade="all, delete-orphan")

class KPIIndicator(Base):
    __tablename__ = "quality_kpi_indicators"

    id = Column(Integer, primary_key=True, index=True)
    processus_id = Column(Integer, ForeignKey("quality_kpi_processus.id"), nullable=False)
    name = Column(String(255), nullable=False)

    processus = relationship("KPIProcessus", back_populates="indicators")
    yearly_targets = relationship("KPIYearlyTarget", back_populates="indicator", cascade="all, delete-orphan")
    values = relationship("KPIValue", back_populates="indicator", cascade="all, delete-orphan")

class KPIYearlyTarget(Base):
    __tablename__ = "quality_kpi_yearly_targets"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("quality_kpi_indicators.id"), nullable=False)
    year = Column(Integer, nullable=False)
    frequency = Column(String(50), nullable=True)
    
    target_raw = Column(String(100), nullable=True)
    target_numeric = Column(Float, nullable=True)
    target_numeric_max = Column(Float, nullable=True)
    operator = Column(Enum(KPIOperator), nullable=True)

    indicator = relationship("KPIIndicator", back_populates="yearly_targets")

    __table_args__ = (
        UniqueConstraint('indicator_id', 'year', name='uix_kpi_target_indicator_year'),
    )

class KPIValue(Base):
    __tablename__ = "quality_kpi_values"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("quality_kpi_indicators.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    value_raw = Column(String(100), nullable=True)
    value_numeric = Column(Float, nullable=True)

    indicator = relationship("KPIIndicator", back_populates="values")

    __table_args__ = (
        UniqueConstraint('indicator_id', 'year', 'month', name='uix_kpi_value_indicator_year_month'),
    )
