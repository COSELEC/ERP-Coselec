from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class NormCategory(Base):
    __tablename__ = "norm_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)

    norms = relationship("Norm", back_populates="category", cascade="all, delete-orphan")

class Norm(Base):
    __tablename__ = "norms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, nullable=False, unique=True)
    title = Column(String, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("norm_categories.id"), nullable=False)

    category = relationship("NormCategory", back_populates="norms")
    versions = relationship("NormVersion", back_populates="norm", cascade="all, delete-orphan")

class NormVersion(Base):
    __tablename__ = "norm_versions"

    id = Column(Integer, primary_key=True, index=True)
    norm_id = Column(Integer, ForeignKey("norms.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    norm = relationship("Norm", back_populates="versions")
