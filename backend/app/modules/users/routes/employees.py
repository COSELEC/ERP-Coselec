from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.users.models.employee import Employee
from app.models.notification import NotificationType
from app.modules.users.models.user import User
from app.services.notification import create_notification

from app.modules.users.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse
)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


def _employee_label(employee: Employee) -> str:
    full_name = f"{employee.first_name or ''} {employee.last_name or ''}".strip()
    if full_name:
        return full_name

    if employee.matricule:
        return employee.matricule

    return f"Employe #{employee.id}"


@router.get(
    "",
    response_model=list[EmployeeResponse]
)
def get_employees(
    _: None = Depends(check_permission("employees.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Employee).all()

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
        db.query(Employee)
        .filter(Employee.id == employee_id)
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
    employee: EmployeeCreate,
    _: None = Depends(check_permission("employees.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_employee = Employee(
        **employee.model_dump()
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Employe cree: {_employee_label(new_employee)}",
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
    employee_data: EmployeeCreate,
    _: None = Depends(check_permission("employees.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    for key, value in employee_data.model_dump().items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Employe mis a jour: {_employee_label(employee)}",
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
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    db.delete(employee)

    db.commit()

    deleted_label = _employee_label(employee)

    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"Employe supprime: {deleted_label}",
        type=NotificationType.WARNING,
        reference_id=employee.id
    )

    return {
        "message": "Employee deleted successfully"
    }
