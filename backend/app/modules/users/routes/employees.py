from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db


from app.models.notification import NotificationType
from app.modules.users.models.user import User
from app.services.notification import create_notification

from app.modules.users.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    OrgChartNode
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


def _employee_label(user: User) -> str:
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if full_name:
        return full_name

    if user.matricule:
        return user.matricule

    return f"Employé #{user.id}"


@router.get(
    "",
    response_model=list[EmployeeResponse]
)
def get_employees(
    _: None = Depends(check_permission("employees.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(User).options(joinedload(User.documents)).all()

@router.get(
    "/org-chart",
    response_model=list[OrgChartNode]
)
def get_org_chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employees = db.query(User).options(joinedload(User.department)).all()
    
    employee_dict = {}
    root_nodes = []
    
    for emp in employees:
        employee_dict[emp.id] = OrgChartNode(
            id=emp.id,
            name=f"{emp.first_name or ''} {emp.last_name or ''}".strip() or f"Employé #{emp.id}",
            position=emp.position or "",
            department=emp.department.name if emp.department else "Sans département",
            email=emp.email,
            phone=emp.phone,
            matricule=emp.matricule,
            status=emp.status,
            manager_id=emp.manager_id,
            children=[]
        )
        
    for emp in employees:
        node = employee_dict[emp.id]
        if emp.manager_id and emp.manager_id in employee_dict:
            employee_dict[emp.manager_id].children.append(node)
        else:
            root_nodes.append(node)
            
    return root_nodes

@router.post("/{user_id}/signature")
async def upload_employee_signature(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    from app.services.storage import upload_file_to_minio
    import uuid
    
    employee = db.query(User).filter(User.id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employé introuvable")
        
    ext = file.filename.split('.')[-1]
    filename = f"signatures/{user_id}_{uuid.uuid4().hex}.{ext}"
    
    file_url = upload_file_to_minio(file, filename)
    
    employee.signature_url = file_url
    db.commit()
    
    return {"signature_url": file_url}

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def get_employee(
    employee_id: int,
    _: None = Depends(check_permission("employees.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(User)
        .filter(User.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee

@router.post(
    "",
    response_model=EmployeeResponse
)
def create_employee(
    user_data: EmployeeCreate,
    _: None = Depends(check_permission("employees.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dumped_data = user_data.model_dump(exclude_unset=True)
    supervised_ids = dumped_data.pop("supervised_employee_ids", None)
    
    new_employee = User(**dumped_data)
    if not new_employee.name:
        new_employee.name = f"{new_employee.first_name or ''} {new_employee.last_name or ''}".strip() or new_employee.email
    db.add(new_employee)

    try:
        db.commit()
        db.refresh(new_employee)
        
        if supervised_ids is not None:
            db.query(User).filter(User.id.in_(supervised_ids)).update({"manager_id": new_employee.id}, synchronize_session=False)
            db.commit()
            
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Un employé avec cet email ou ce matricule existe déjà")

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Employé créé: {_employee_label(new_employee)}",
        type=NotificationType.INFO,
        reference_id=new_employee.id
    )

    return new_employee

@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    _: None = Depends(check_permission("employees.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(User)
        .filter(User.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    dumped_data = employee_data.model_dump(exclude_unset=True)
    supervised_ids = dumped_data.pop("supervised_employee_ids", None)

    if "manager_id" in dumped_data and dumped_data["manager_id"] == employee_id:
        raise HTTPException(status_code=400, detail="Un employé ne peut pas être son propre responsable")

    if supervised_ids is not None and employee_id in supervised_ids:
        raise HTTPException(status_code=400, detail="Un employé ne peut pas être dans sa propre liste de subordonnés")

    for key, value in dumped_data.items():
        setattr(employee, key, value)
        
    full_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
    if full_name:
        employee.name = full_name

    try:
        db.commit()
        db.refresh(employee)
        
        if supervised_ids is not None:
            db.query(User).filter(User.manager_id == employee.id).filter(~User.id.in_(supervised_ids)).update({"manager_id": None}, synchronize_session=False)
            if supervised_ids:
                db.query(User).filter(User.id.in_(supervised_ids)).update({"manager_id": employee.id}, synchronize_session=False)
            db.commit()
            db.refresh(employee)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Un employé avec cet email ou ce matricule existe déjà")

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Employé mis à jour: {_employee_label(employee)}",
        type=NotificationType.INFO,
        reference_id=employee.id
    )

    return employee


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    _: None = Depends(check_permission("employees.delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(User)
        .filter(User.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    deleted_label = _employee_label(employee)
    del_id = employee.id

    try:
        db.delete(employee)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer l'employé : il est toujours assigné à des projets, tâches, ou possède des documents liés. Veuillez les réassigner ou les supprimer d'abord."
        )

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Employé supprimé: {deleted_label}",
        type=NotificationType.WARNING,
        reference_id=del_id
    )

    return {
        "message": "Employee deleted successfully"
    }

