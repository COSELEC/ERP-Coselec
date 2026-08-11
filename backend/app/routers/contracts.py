from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security.auth import get_current_user, check_permission
from app.modules.users.models.user import User
from app.models.hr.contract import Contract
from app.modules.users.models.user import User
from app.models.notification import NotificationType
from app.services.notification import create_notification
from app.schemas.hr.hr import ContractCreate, ContractUpdate, ContractResponse

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"]
)

@router.get("", response_model=list[ContractResponse])
def get_contracts(
    _: None = Depends(check_permission("contracts.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Contract).all()

@router.post("", response_model=ContractResponse)
def create_contract(
    contract_data: ContractCreate,
    _: None = Depends(check_permission("contracts.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == contract_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_contract = Contract(**contract_data.model_dump())
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Nouveau contrat créé pour l'employé {user.first_name} {user.last_name}",
        type=NotificationType.INFO,
        reference_id=new_contract.id
    )
    return new_contract

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    _: None = Depends(check_permission("contracts.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    for key, value in contract_data.model_dump(exclude_unset=True).items():
        setattr(contract, key, value)

    db.commit()
    db.refresh(contract)
    return contract

@router.delete("/{contract_id}")
def delete_contract(
    contract_id: int,
    _: None = Depends(check_permission("contracts.delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    db.delete(contract)
    db.commit()
    return {"message": "Contract deleted successfully"}
