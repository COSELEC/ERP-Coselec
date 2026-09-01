from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import Optional
from app.repositories.norm_repository import NormRepository
from app.services.storage import StorageService
from app.models.norm import Norm, NormVersion

class NormService:
    def __init__(self, db: Session, storage_service: StorageService):
        self.db = db
        self.repository = NormRepository(db)
        self.storage_service = storage_service

    def upload_new_version(self, norm_id: int, file: UploadFile, version_number: int) -> NormVersion:
        norm = self.repository.get_norm_by_id(norm_id)
        if not norm:
            raise HTTPException(status_code=404, detail="Norme introuvable")

        try:
            file_path = self.storage_service.save_file(file, path="norms")

            self.repository.deactivate_active_version(norm_id)

            new_version = NormVersion(
                norm_id=norm_id,
                version_number=version_number,
                file_url=file_path,
                is_active=True
            )
            self.repository.create_norm_version(new_version)
            self.db.commit()
            self.db.refresh(new_version)
            return new_version
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def create_norm_with_file(self, code: str, title: str, category_id: Optional[int], file: UploadFile) -> Norm:
        try:
            file_path = self.storage_service.save_file(file, path="norms")

            new_norm = Norm(code=code, title=title, category_id=category_id)
            self.repository.create_norm(new_norm)

            new_version = NormVersion(
                norm_id=new_norm.id,
                version_number=1,
                file_url=file_path,
                is_active=True
            )
            self.repository.create_norm_version(new_version)
            
            self.db.commit()
            self.db.refresh(new_norm)
            return new_norm
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def delete_norm(self, norm_id: int) -> bool:
        return self.repository.delete_norm(norm_id)

