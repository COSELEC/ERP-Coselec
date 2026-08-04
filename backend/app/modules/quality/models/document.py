import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class QualityDocStatus(str, enum.Enum):
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"

class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

from sqlalchemy import Table

quality_document_visible_roles = Table(
    'quality_document_visible_roles', Base.metadata,
    Column('document_id', Integer, ForeignKey('quality_documents.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

class QualityDocument(Base):
    __tablename__ = "quality_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(QualityDocStatus), default=QualityDocStatus.IN_REVIEW, nullable=False)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="desc(DocumentVersion.version_number)")
    role_reviews = relationship("DocumentRoleReview", back_populates="document", cascade="all, delete-orphan")
    visible_roles = relationship("Role", secondary=quality_document_visible_roles)

class DocumentVersion(Base):
    __tablename__ = "quality_document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("quality_documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    r2_file_key = Column(String, nullable=False) # Key in R2
    original_filename = Column(String, nullable=False)
    
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("QualityDocument", back_populates="versions")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])

class DocumentRoleReview(Base):
    __tablename__ = "quality_document_role_reviews"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("quality_documents.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    comment = Column(Text, nullable=True)
    
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    document = relationship("QualityDocument", back_populates="role_reviews")
    role = relationship("Role", foreign_keys=[role_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
