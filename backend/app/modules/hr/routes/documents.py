import os
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security.auth import get_current_user, check_permission
from app.modules.users.models.user import User
from app.modules.users.models.user import User
from app.models.hr.document import EmployeeDocument, DocumentCategory
from app.services.storage import upload_file_to_minio, get_file_url_from_minio, delete_file_from_minio
from app.schemas.hr.hr import DocumentResponse

router = APIRouter(
    prefix="/users",
    tags=["User Documents"]
)


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    _: None = Depends(check_permission("documents.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    try:
        url = get_file_url_from_minio(doc.storage_path)
        return RedirectResponse(url)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Erreur lors de la récupération du fichier")

@router.get("/{user_id}/documents", response_model=list[DocumentResponse])
def get_employee_documents(
    user_id: int,
    _: None = Depends(check_permission("documents.read")), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employé introuvable")

    documents = db.query(EmployeeDocument).filter(EmployeeDocument.user_id == user_id).all()
    return documents

@router.post("/{user_id}/documents", response_model=DocumentResponse)
def upload_employee_document(
    user_id: int,
    file: UploadFile = File(...),
    category: DocumentCategory = Form(...),
    numero: Optional[str] = Form(None),
    expiry_date: Optional[date] = Form(None),
    _: None = Depends(check_permission("documents.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employé introuvable")

    file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"emp_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

    try:
        storage_path = upload_file_to_minio(file, unique_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

    new_doc = EmployeeDocument(
        user_id=user_id,
        category=category,
        file_name=file.filename, 
        storage_path=storage_path, 
        mime_type=file.content_type,
        numero=numero,
        expiry_date=expiry_date,
        is_verified=False
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return new_doc

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    _: None = Depends(check_permission("documents.delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    delete_file_from_minio(doc.storage_path)

    db.delete(doc)
    db.commit()
    return {"message": "Document supprimé"}
