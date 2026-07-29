from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.project.assignment import ProjectAssignment
from app.models.project.project import Project
from app.modules.users.models.employee import Employee
from app.schemas.project.assignment import AssignmentCreate, AssignmentUpdate, AssignmentResponse
from fastapi import BackgroundTasks
from app.modules.users.models.user import User
from app.services.event_notifier import notify_user
from app.models.notification import NotificationType
from typing import List
from datetime import date
from app.services.availability import is_employee_on_leave

router = APIRouter(tags=["Project Assignments"])

def get_employee_active_allocation(db: Session, employee_id: int, exclude_assignment_id: int = None) -> float:
    today = date.today()
    query = db.query(ProjectAssignment).filter(ProjectAssignment.employee_id == employee_id)
    assignments = query.all()
    
    total = 0.0
    for a in assignments:
        if exclude_assignment_id and a.id == exclude_assignment_id:
            continue
        # Check if active
        if a.start_date <= today and (a.end_date is None or a.end_date >= today):
            total += a.allocation
            
    return total

@router.get("/projects/{project_id}/assignments", response_model=List[AssignmentResponse])
def get_project_assignments(project_id: int, db: Session = Depends(get_db)):
    assignments = db.query(ProjectAssignment).options(
        joinedload(ProjectAssignment.employee)
    ).filter(ProjectAssignment.project_id == project_id).all()
    return assignments

@router.post("/projects/{project_id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_project_assignment(project_id: int, assignment: AssignmentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check leave status
    if is_employee_on_leave(db, assignment.employee_id, assignment.start_date, assignment.end_date):
        raise HTTPException(status_code=400, detail="Employé en congé sur cette période")

    # Check duplicate
    existing = db.query(ProjectAssignment).filter(
        ProjectAssignment.project_id == project_id,
        ProjectAssignment.employee_id == assignment.employee_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee is already assigned to this project")

    # Check allocation
    today = date.today()
    is_active = assignment.start_date <= today and (assignment.end_date is None or assignment.end_date >= today)
    if is_active:
        current_allocation = get_employee_active_allocation(db, assignment.employee_id)
        if current_allocation + assignment.allocation > 100:
            raise HTTPException(
                status_code=400, 
                detail=f"Allocation exceeds 100%. Employee currently has {current_allocation}% active allocation."
            )

    db_assignment = ProjectAssignment(
        project_id=project_id,
        **assignment.model_dump()
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    # Reload with employee
    db_assignment = db.query(ProjectAssignment).options(
        joinedload(ProjectAssignment.employee)
    ).filter(ProjectAssignment.id == db_assignment.id).first()
    
    if employee.email:
        user = db.query(User).filter(User.email == employee.email).first()
        if user:
            background_tasks.add_task(
                notify_user,
                user.id,
                f"Vous avez été assigné au projet: {project.name}",
                NotificationType.INFO,
                db_assignment.id
            )

    return db_assignment

@router.patch("/projects/assignments/{assignment_id}", response_model=AssignmentResponse)
def update_project_assignment(assignment_id: int, assignment_update: AssignmentUpdate, db: Session = Depends(get_db)):
    db_assignment = db.query(ProjectAssignment).filter(ProjectAssignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_data = assignment_update.model_dump(exclude_unset=True)
    
    # Check allocation if changing dates or allocation
    if "allocation" in update_data or "start_date" in update_data or "end_date" in update_data:
        new_alloc = update_data.get("allocation", db_assignment.allocation)
        new_start = update_data.get("start_date", db_assignment.start_date)
        new_end = update_data.get("end_date", db_assignment.end_date)
        
        # Check leave status
        if is_employee_on_leave(db, db_assignment.employee_id, new_start, new_end):
            raise HTTPException(status_code=400, detail="Employé en congé sur cette période")
        
        today = date.today()
        is_active = new_start <= today and (new_end is None or new_end >= today)
        
        if is_active:
            current_allocation = get_employee_active_allocation(db, db_assignment.employee_id, exclude_assignment_id=assignment_id)
            if current_allocation + new_alloc > 100:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Allocation exceeds 100%. Employee currently has {current_allocation}% active allocation elsewhere."
                )

    for key, value in update_data.items():
        setattr(db_assignment, key, value)
        
    db.commit()
    db.refresh(db_assignment)
    
    db_assignment = db.query(ProjectAssignment).options(
        joinedload(ProjectAssignment.employee)
    ).filter(ProjectAssignment.id == db_assignment.id).first()
    
    return db_assignment

@router.delete("/projects/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_assignment(assignment_id: int, db: Session = Depends(get_db)):
    db_assignment = db.query(ProjectAssignment).filter(ProjectAssignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    db.delete(db_assignment)
    db.commit()
    return None

@router.get("/employees/{employee_id}/assignments", response_model=List[AssignmentResponse])
def get_employee_assignments(employee_id: int, db: Session = Depends(get_db)):
    assignments = db.query(ProjectAssignment).options(
        joinedload(ProjectAssignment.project)
    ).filter(ProjectAssignment.employee_id == employee_id).all()
    return assignments
