from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.modules.quality.models.document import QualityDocStatus, ReviewStatus

class DocumentRoleReviewResponse(BaseModel):
    id: int
    role_id: int
    status: ReviewStatus
    comment: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentVersionResponse(BaseModel):
    id: int
    version_number: int
    original_filename: str
    r2_file_key: str
    uploaded_by_id: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QualityDocumentBase(BaseModel):
    title: str
    description: Optional[str] = None

class QualityDocumentCreate(QualityDocumentBase):
    role_ids: List[int]

class QualityDocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class QualityDocumentResponse(QualityDocumentBase):
    id: int
    status: QualityDocStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    versions: List[DocumentVersionResponse]
    role_reviews: List[DocumentRoleReviewResponse]

    model_config = ConfigDict(from_attributes=True)

class ReviewSubmit(BaseModel):
    status: ReviewStatus
    comment: Optional[str] = None
