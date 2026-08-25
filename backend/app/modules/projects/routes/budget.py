from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.project.budget import ProjectBudget
from app.models.project.expense import ProjectExpense, ExpenseStatus
from pydantic import BaseModel, ConfigDict, computed_field, Field
from fastapi import BackgroundTasks
from app.services.event_notifier import notify_users_by_role
from app.models.notification import NotificationType
from datetime import datetime, date
from typing import List
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User

router = APIRouter(prefix="/projects/{project_id}/budgets", tags=["Project Budgets"])

class BudgetCreate(BaseModel):
    category: str
    allocated_amount: float = Field(..., gt=0)
    currency: str = "XOF"

class BudgetResponse(BudgetCreate):
    id: int
    project_id: int
    created_at: datetime
    
    consumed: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class ExpenseCreate(BaseModel):
    budget_id: int | None = None
    amount: float = Field(..., gt=0)
    date_incurred: date
    description: str | None = None

class ExpenseResponse(ExpenseCreate):
    id: int
    project_id: int
    status: str
    proof_document_url: str | None = None
    model_config = ConfigDict(from_attributes=True)

class ExpenseUpdate(BaseModel):
    status: ExpenseStatus

class BudgetUpdate(BaseModel):
    category: str | None = None
    allocated_amount: float | None = None

@router.get("", response_model=List[BudgetResponse])
def get_budgets(
    project_id: int, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    return db.query(ProjectBudget).options(joinedload(ProjectBudget.expenses)).filter(ProjectBudget.project_id == project_id).offset(skip).limit(limit).all()

@router.post("", response_model=BudgetResponse)
def create_budget(project_id: int, budget: BudgetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        raise HTTPException(status_code=403, detail="Non autorisé.")

    db_budget = ProjectBudget(
        project_id=project_id,
        category=budget.category,
        allocated_amount=budget.allocated_amount,
        currency=budget.currency
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(project_id: int, budget_id: int, update_data: BudgetUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        raise HTTPException(status_code=403, detail="Non autorisé.")
    db_budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id, ProjectBudget.project_id == project_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    if update_data.category is not None:
        db_budget.category = update_data.category
    if update_data.allocated_amount is not None:
        db_budget.allocated_amount = update_data.allocated_amount
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.delete("/{budget_id}")
def delete_budget(project_id: int, budget_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_names = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in role_names and "DIRECTION" not in role_names:
        raise HTTPException(status_code=403, detail="Non autorisé.")
    db_budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id, ProjectBudget.project_id == project_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    if db.query(ProjectExpense).filter(ProjectExpense.budget_id == budget_id).first():
        raise HTTPException(status_code=400, detail="Impossible de supprimer un budget avec des dépenses")
    db.delete(db_budget)
    db.commit()
    return {"message": "Budget deleted successfully"}

@router.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    project_id: int, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    db: Session = Depends(get_db)
):
    return db.query(ProjectExpense).filter(ProjectExpense.project_id == project_id).offset(skip).limit(limit).all()

@router.post("/expenses", response_model=ExpenseResponse)
def add_expense(project_id: int, expense: ExpenseCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if expense.budget_id:
        budget = db.query(ProjectBudget).with_for_update().filter(ProjectBudget.id == expense.budget_id, ProjectBudget.project_id == project_id).first()
        if not budget:
            raise HTTPException(status_code=404, detail="Budget introuvable pour ce projet")
        if expense.amount > budget.remaining_amount:
            raise HTTPException(status_code=400, detail="Le montant de la dépense dépasse le budget alloué")
            
    db_expense = ProjectExpense(
        project_id=project_id,
        budget_id=expense.budget_id,
        amount=expense.amount,
        date_incurred=expense.date_incurred,
        description=expense.description
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    background_tasks.add_task(
        notify_users_by_role,
        ["Admin", "Manager"],
        f"Nouvelle dépense soumise pour le projet {project_id} ({expense.amount} {expense.currency if hasattr(expense, 'currency') else ''})",
        NotificationType.INFO,
        db_expense.id
    )

    return db_expense

@router.patch("/expenses/{expense_id}/status", response_model=ExpenseResponse)
def update_expense_status(project_id: int, expense_id: int, update_data: ExpenseUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_expense = db.query(ProjectExpense).filter(ProjectExpense.id == expense_id, ProjectExpense.project_id == project_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    
    if db_expense.status != ExpenseStatus.PENDING:
        raise HTTPException(status_code=400, detail="Seules les dépenses en attente peuvent être modifiées")
    
    db_expense.status = update_data.status
    db.commit()
    db.refresh(db_expense)
    
    background_tasks.add_task(
        notify_users_by_role,
        ["Admin", "Manager"],
        f"Le statut de la dépense {expense_id} du projet {project_id} est maintenant : {update_data.status.value}",
        NotificationType.INFO,
        db_expense.id
    )

    return db_expense
