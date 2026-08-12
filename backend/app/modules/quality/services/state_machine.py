from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.modules.quality.models.document import (
    QualityDocument, DocumentVersion, DocumentRoleReview,
    QualityDocStatus, ReviewStatus
)
from app.modules.users.models.user import User
from app.services.storage import upload_file_to_minio, delete_file_from_minio
from app.services.notification import create_notification
from app.models.notification import NotificationType
import os

def notify_reviewer(db: Session, role_id: int, user_id: int | None, message: str, reference_id: int):
    if user_id:
        create_notification(db, user_id, message, NotificationType.INFO, reference_id)
    else:
        users = db.query(User).filter(User.roles.any(id=role_id)).all()
        for u in users:
            create_notification(db, u.id, message, NotificationType.INFO, reference_id)

def create_document(
    db: Session,
    title: str,
    description: str | None,
    reviewers: list[dict],
    file: UploadFile,
    current_user: User
) -> QualityDocument:
    
    doc = QualityDocument(
        title=title,
        description=description,
        status=QualityDocStatus.IN_REVIEW,
        created_by_id=current_user.id
    )
    db.add(doc)
    db.flush() 

    for rev_data in reviewers:
        role_id = rev_data.get("role_id")
        user_id = rev_data.get("user_id")
        
        rev = DocumentRoleReview(
            document_id=doc.id,
            role_id=role_id,
            assigned_user_id=user_id,
            status=ReviewStatus.PENDING
        )
        db.add(rev)
        
        notify_reviewer(db, role_id, user_id, f"Nouveau document qualité à valider: {title}", doc.id)
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    r2_key = f"quality_docs/{doc.id}/v1/{title}{ext}"
    upload_file_to_minio(file, r2_key)

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        r2_file_key=r2_key,
        original_filename=file.filename or title,
        uploaded_by_id=current_user.id
    )
    db.add(version)
    
    db.commit()
    db.refresh(doc)
    return doc

def submit_review(
    db: Session,
    document_id: int,
    review_id: int,
    status: ReviewStatus,
    comment: str | None,
    current_user: User
):
    doc = db.query(QualityDocument).filter(QualityDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
        
    review = db.query(DocumentRoleReview).filter(
        DocumentRoleReview.id == review_id,
        DocumentRoleReview.document_id == document_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Revue introuvable")
        
    if doc.created_by_id == current_user.id:
        raise HTTPException(status_code=403, detail="Le créateur du document ne peut pas valider sa propre version")
        
    if review.assigned_user_id:
        if review.assigned_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Vous n'êtes pas assigné pour valider cette étape")
    else:
        if not any(r.id == review.role_id for r in current_user.roles):
            raise HTTPException(status_code=403, detail="Vous n'avez pas le rôle requis pour soumettre cette revue")
            
    if review.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=400, detail="Déjà revu")
        
    review.status = status
    review.comment = comment
    review.reviewed_by_id = current_user.id
    import datetime
    review.reviewed_at = datetime.datetime.utcnow()
    
    if status == ReviewStatus.REJECTED:
        doc.status = QualityDocStatus.REJECTED
        create_notification(db, doc.created_by_id, f"Document rejeté: {doc.title}", NotificationType.WARNING, doc.id)
        
    elif status == ReviewStatus.APPROVED:
        all_reviews = db.query(DocumentRoleReview).filter(DocumentRoleReview.document_id == document_id).all()
        all_approved = all(r.status == ReviewStatus.APPROVED or r.id == review.id for r in all_reviews)
        
        if all_approved:
            doc.status = QualityDocStatus.APPROVED
            create_notification(db, doc.created_by_id, f"Document totalement approuvé: {doc.title}", NotificationType.INFO, doc.id)
            
            versions = sorted(doc.versions, key=lambda v: v.version_number)
            if len(versions) > 1:
                for v in versions[:-1]:
                    delete_file_from_minio(v.r2_file_key)

    db.commit()
    db.refresh(doc)
    return doc

def upload_new_version(
    db: Session,
    document_id: int,
    file: UploadFile,
    current_user: User
):
    doc = db.query(QualityDocument).filter(QualityDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
        
    if doc.status != QualityDocStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Nouvelle version possible uniquement si rejetée")
        
    is_admin = any(r.name in ["Admin", "Qualité", "Qualite"] for r in current_user.roles)
    is_creator = doc.created_by_id == current_user.id
    
    is_reviewer = False
    for r in doc.role_reviews:
        if r.assigned_user_id == current_user.id:
            is_reviewer = True
            break
        if not r.assigned_user_id and any(role.id == r.role_id for role in current_user.roles):
            is_reviewer = True
            break

    if not (is_admin or is_creator or is_reviewer):
        raise HTTPException(status_code=403, detail="Vous n'avez pas l'autorisation de télécharger une nouvelle version")
        
    doc.status = QualityDocStatus.IN_REVIEW
    
    reviews = db.query(DocumentRoleReview).filter(DocumentRoleReview.document_id == document_id).all()
    
    if doc.created_by_id != current_user.id:
        old_creator_id = doc.created_by_id
        doc.created_by_id = current_user.id
        swapped = False
        for rev in reviews:
            if rev.assigned_user_id == current_user.id:
                rev.assigned_user_id = old_creator_id
                swapped = True
                break
        if not swapped:
            for rev in reviews:
                if not rev.assigned_user_id and any(role.id == rev.role_id for role in current_user.roles):
                    rev.assigned_user_id = old_creator_id
                    swapped = True
                    break

    for rev in reviews:
        rev.status = ReviewStatus.PENDING
        rev.comment = None
        rev.reviewed_by_id = None
        rev.reviewed_at = None
        notify_reviewer(db, rev.role_id, rev.assigned_user_id, f"Nouvelle version à valider: {doc.title}", doc.id)
        
    next_v = max((v.version_number for v in doc.versions), default=0) + 1
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    r2_key = f"quality_docs/{doc.id}/v{next_v}/{doc.title}{ext}"
    upload_file_to_minio(file, r2_key)

    version = DocumentVersion(
        document_id=doc.id,
        version_number=next_v,
        r2_file_key=r2_key,
        original_filename=file.filename or doc.title,
        uploaded_by_id=current_user.id
    )
    db.add(version)
    
    db.commit()
    db.refresh(doc)
    return doc

def delete_document(db: Session, document_id: int, current_user: User):
    doc = db.query(QualityDocument).filter(QualityDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
        
    is_admin = any(r.name in ["Admin", "Qualité"] for r in current_user.roles)
    if doc.created_by_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Vous n'avez pas la permission de supprimer ce document")
        
    for version in doc.versions:
        try:
            delete_file_from_minio(version.r2_file_key)
        except Exception as e:
            print(f"Error deleting file from R2: {e}")
            
    db.delete(doc)
    db.commit()
    return True
