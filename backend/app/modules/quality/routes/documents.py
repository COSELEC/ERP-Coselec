import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User
from app.modules.quality.models.document import QualityDocument, DocumentRoleReview
from app.modules.quality.schemas.document import QualityDocumentResponse, ReviewSubmit
from app.modules.quality.services.state_machine import (
    create_document,
    submit_review,
    upload_new_version
)

router = APIRouter(prefix="/quality/documents", tags=["Quality"])

@router.get("/available-roles")
def api_get_available_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.modules.users.models.role import Role
    roles = db.query(Role).all()
    result = []
    for r in roles:
        users = [{"id": u.id, "name": u.name} for u in r.users if u.is_active]
        result.append({"id": r.id, "name": r.name, "users": users})
    return result

@router.get("", response_model=list[QualityDocumentResponse])
def api_get_documents(
    filter_pending_for_me: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(QualityDocument)
    
    if filter_pending_for_me:
        user_role_ids = [r.id for r in current_user.roles]
        if not user_role_ids:
            return []
            
        # Documents that have a pending review for me specifically OR for one of my roles
        query = query.join(QualityDocument.role_reviews).filter(
            DocumentRoleReview.status == "PENDING",
            or_(
                DocumentRoleReview.assigned_user_id == current_user.id,
                and_(
                    DocumentRoleReview.assigned_user_id == None,
                    DocumentRoleReview.role_id.in_(user_role_ids)
                )
            )
        )
        
    return query.order_by(QualityDocument.created_at.desc()).all()

@router.post("", response_model=QualityDocumentResponse)
def api_create_document(
    title: str = Form(...),
    description: str = Form(None),
    reviewers_json: str = Form(...), # JSON string of list of dicts: [{"role_id": 1, "user_id": null}, ...]
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        reviewers_list = json.loads(reviewers_json)
        if not isinstance(reviewers_list, list):
            raise ValueError
    except:
        raise HTTPException(status_code=400, detail="reviewers_json must be a JSON list of objects")

    doc = create_document(db, title, description, reviewers_list, file, current_user)
    return doc

@router.get("/{doc_id}", response_model=QualityDocumentResponse)
def api_get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(QualityDocument).filter(QualityDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/{doc_id}/versions", response_model=QualityDocumentResponse)
def api_upload_new_version(
    doc_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return upload_new_version(db, doc_id, file, current_user)

@router.post("/{doc_id}/reviews/{review_id}", response_model=QualityDocumentResponse)
def api_submit_review(
    doc_id: int,
    review_id: int,
    payload: ReviewSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return submit_review(db, doc_id, review_id, payload.status, payload.comment, current_user)

@router.get("/{doc_id}/download/{version_id}")
def api_download_document(
    doc_id: int,
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(QualityDocument).filter(QualityDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    version = next((v for v in doc.versions if v.id == version_id), None)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    from app.services.storage import get_presigned_url
    url = get_presigned_url(version.r2_file_key, version.original_filename)
    return {"url": url}

@router.delete("/{doc_id}")
def api_delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.modules.quality.services.state_machine import delete_document
    delete_document(db, doc_id, current_user)
    return {"message": "Document deleted successfully"}
