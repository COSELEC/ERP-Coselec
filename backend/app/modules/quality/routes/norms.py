from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.norm import NormResponse, NormCreate, NormVersionResponse, NormCategoryResponse
from app.models.norm import Norm
from app.repositories.norm_repository import NormRepository
from app.services.norm_service import NormService
from app.services.storage import StorageService, LocalStorageStrategy

router = APIRouter(prefix="/norms", tags=["Norms (GED)"])

def get_storage_service():
    strategy = LocalStorageStrategy()
    return StorageService(strategy)

def get_norm_service(db: Session = Depends(get_db), storage_service: StorageService = Depends(get_storage_service)):
    return NormService(db, storage_service)

def get_norm_repository(db: Session = Depends(get_db)):
    return NormRepository(db)

@router.get("", response_model=List[NormResponse])
def get_all_norms(repository: NormRepository = Depends(get_norm_repository)):
    return repository.get_all_active_norms()

@router.get("/categories", response_model=List[NormCategoryResponse])
def get_categories(repository: NormRepository = Depends(get_norm_repository)):
    return repository.get_all_categories()

@router.post("", response_model=NormResponse)
def create_norm(
    code: str = Form(...),
    title: str = Form(...),
    category_id: int = Form(...),
    file: UploadFile = File(...),
    service: NormService = Depends(get_norm_service)
):
    return service.create_norm_with_file(code, title, category_id, file)

@router.post("/{norm_id}/versions", response_model=NormVersionResponse)
def upload_norm_version(
    norm_id: int, 
    version_number: int = Form(...), 
    file: UploadFile = File(...),
    service: NormService = Depends(get_norm_service)
):
    return service.upload_new_version(norm_id, file, version_number)

@router.get("/{norm_id}/history", response_model=List[NormVersionResponse])
def get_norm_history(norm_id: int, repository: NormRepository = Depends(get_norm_repository)):
    return repository.get_norm_history(norm_id)

@router.delete("/{norm_id}", status_code=204)
def delete_norm(norm_id: int, service: NormService = Depends(get_norm_service)):
    success = service.delete_norm(norm_id)
    if not success:
        raise HTTPException(status_code=404, detail="Norme non trouvée")
