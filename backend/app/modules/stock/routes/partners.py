from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.stock.models.partner import Partner
from app.modules.users.models.user import User

from app.modules.stock.schemas.partner import (
    PartnerCreate,
    PartnerUpdate,
    PartnerResponse
)

router = APIRouter(
    prefix="/partners",
    tags=["Partners"]
)


@router.get("/", response_model=list[PartnerResponse])
def get_partners(
    _: None = Depends(check_permission("stock.read")),
    db: Session = Depends(get_db)
):
    return db.query(Partner).all()


@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: int,
    _: None = Depends(check_permission("stock.read")),
    
    db: Session = Depends(get_db)
):
    partner = (
        db.query(Partner)
        .filter(Partner.id == partner_id)
        .first()
    )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found"
        )

    return partner


@router.post(
    "/",
    response_model=PartnerResponse,
    status_code=201
)
def create_partner(
    partner: PartnerCreate,
    _: None = Depends(check_permission("stock.create")),
    
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Partner)
        .filter(Partner.code == partner.code)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Partner code already exists"
        )

    new_partner = Partner(
        **partner.model_dump()
    )

    db.add(new_partner)
    db.commit()
    db.refresh(new_partner)

    return new_partner


@router.put(
    "/{partner_id}",
    response_model=PartnerResponse
)
def update_partner(
    partner_id: int,
    partner: PartnerUpdate,
    _: None = Depends(check_permission("stock.update")),
    
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Partner)
        .filter(Partner.id == partner_id)
        .first()
    )

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Partner not found"
        )

    data = partner.model_dump(
        exclude_unset=True
    )

    if "code" in data:
        code_exists = (
            db.query(Partner)
            .filter(
                Partner.code == data["code"],
                Partner.id != partner_id
            )
            .first()
        )

        if code_exists:
            raise HTTPException(
                status_code=400,
                detail="Partner code already exists"
            )

    for key, value in data.items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)

    return existing


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(
    partner_id: int,
    _: None = Depends(check_permission("stock.delete")),
    db: Session = Depends(get_db)
):
    partner = db.get(Partner, partner_id)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partenaire non trouvé"
        )

    # VERROU DE SÉCURITÉ : On bloque la suppression si le partenaire est lié à des projets
    if hasattr(partner, 'projects') and partner.projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer ce partenaire car il est rattaché à un ou plusieurs projets actifs."
        )

    db.delete(partner)
    db.commit()
