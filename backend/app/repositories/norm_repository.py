from sqlalchemy.orm import Session
from app.models.norm import Norm, NormVersion, NormCategory
from typing import List, Optional

class NormRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_active_norms(self) -> List[Norm]:
        """Récupère toutes les normes avec uniquement leur version active."""
        return self.db.query(Norm).all()

    def delete_norm(self, norm_id: int) -> bool:
        norm = self.db.query(Norm).filter(Norm.id == norm_id).first()
        if not norm:
            return False
        self.db.delete(norm)
        self.db.commit()
        return True

    def get_all_categories(self) -> List[NormCategory]:
        return self.db.query(NormCategory).all()

    def get_norm_history(self, norm_id: int) -> List[NormVersion]:
        """Récupère l'historique complet des versions d'une norme spécifique."""
        return self.db.query(NormVersion).filter(
            NormVersion.norm_id == norm_id
        ).order_by(NormVersion.created_at.desc()).all()

    def get_norm_by_id(self, norm_id: int) -> Optional[Norm]:
        return self.db.query(Norm).filter(Norm.id == norm_id).first()

    def create_norm(self, norm: Norm) -> Norm:
        self.db.add(norm)
        self.db.flush()
        return norm

    def create_norm_version(self, version: NormVersion) -> NormVersion:
        self.db.add(version)
        self.db.flush()
        return version

    def deactivate_active_version(self, norm_id: int):
        active_version = self.db.query(NormVersion).filter(
            NormVersion.norm_id == norm_id,
            NormVersion.is_active == True
        ).first()
        if active_version:
            active_version.is_active = False
            self.db.add(active_version)
            self.db.flush()
