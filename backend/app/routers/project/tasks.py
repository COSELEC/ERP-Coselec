import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security.auth import check_permission, get_current_user
from app.schemas.project.task import TaskDocumentResponse, TaskResponse, TaskUpdate, TaskCreate
from app.models.project.project import Project
from app.modules.users.models.user import User
from app.models.project.task import Task, TaskStatus
from app.models.hr.document import TaskDocument
from app.services.storage import upload_file_to_minio, get_file_url_from_minio, delete_file_from_minio
router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

#GET
@router.get("", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def get_tasks_by_project(project_id:int, milestone_id: int | None = None, db : Session=Depends(get_db), user_permissions=Depends(check_permission("tasks.read"))):
    query = db.query(Task).filter(Task.project_id==project_id)
    if milestone_id is not None:
        query = query.filter(Task.milestone_id == milestone_id)
    tasks = query.all()
    if len(tasks) ==0:
        return []
    return tasks


@router.get("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def get_task(task_id: int, db: Session=Depends(get_db), user_permissions=Depends(check_permission("tasks.read"))):
    task = db.query(Task).filter(Task.id==task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche non trouvée")
    return task


# POST
@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task_for_project( task_data : TaskCreate, project_id: int, db: Session=Depends(get_db), user_permissions=Depends(check_permission("tasks.create")), current_user=Depends(get_current_user)):
    existing_task = db.query(Task).filter(Task.project_id==project_id,Task.title == task_data.title).count()
    if existing_task>0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail= "Une tâche avec ce titre existe deja dans ce projet")
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    if task_data.assignee_id is not None:
        user= (db.query(User).filter(User.id == task_data.assignee_id)).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé assigné à la tâche non trouvé")
        
        from app.services.availability import is_employee_on_leave
        start = task_data.start_date if task_data.start_date else task_data.due_date
        if is_employee_on_leave(db, task_data.assignee_id, start, task_data.due_date):
            raise HTTPException(status_code=400, detail="Employé en congé sur cette période")

    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    if task_count>100:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Le nombre maximal de tâches par projet a été atteint")
    task = Task(
    **task_data.model_dump(exclude={"project_id"}),
    project_id=project_id,
    author_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

#PATCH
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(project_id: int, task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db), user_permissions=Depends(check_permission("tasks.update"))):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée dans ce projet")
    
    update_data = task_data.model_dump(exclude_unset=True)
    
    if "assignee_id" in update_data or "start_date" in update_data or "due_date" in update_data:
        new_assignee_id = update_data.get("assignee_id", task.assignee_id)
        if new_assignee_id is not None:
            new_start = update_data.get("start_date", task.start_date)
            new_end = update_data.get("due_date", task.due_date)
            start = new_start if new_start else new_end
            if start and new_end:
                from app.services.availability import is_employee_on_leave
                if is_employee_on_leave(db, new_assignee_id, start, new_end):
                    raise HTTPException(status_code=400, detail="Employé en congé sur cette période")

    for field, value in update_data.items():
        setattr(task, field, value)
        
    db.commit()
    db.refresh(task)

    if task.milestone_id and task.status == TaskStatus.DONE:
        from app.models.project.milestone import ProjectMilestone, MilestoneStatus
        from datetime import date
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == task.milestone_id).first()
        if milestone and milestone.status != MilestoneStatus.ACHIEVED:
            incomplete = db.query(Task).filter(
                Task.milestone_id == task.milestone_id,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.ARCHIVED])
            ).count()
            if incomplete == 0:
                milestone.status = MilestoneStatus.ACHIEVED
                milestone.achieved_date = date.today()
                next_milestone = db.query(ProjectMilestone).filter(
                    ProjectMilestone.project_id == project_id,
                    ProjectMilestone.order_index > milestone.order_index
                ).order_by(ProjectMilestone.order_index).first()
                if next_milestone:
                    next_milestone.status = MilestoneStatus.ACTIVE
                db.commit()

    return task


@router.get("/{task_id}/documents", response_model=list[TaskDocumentResponse], status_code=status.HTTP_200_OK)
def get_task_documents(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("tasks.read"))
):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche non trouvée dans ce projet")

    return db.query(TaskDocument).filter(TaskDocument.task_id == task_id).all()


@router.post("/{task_id}/documents", response_model=list[TaskDocumentResponse], status_code=status.HTTP_201_CREATED)
def upload_task_documents(
    project_id: int,
    task_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("tasks.update"))
):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche non trouvée dans ce projet")

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun fichier fourni")

    created_docs: list[TaskDocument] = []
    for file in files:
        if not file.filename:
            continue

        file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
        unique_filename = f"task_{task_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

        try:
            storage_path = upload_file_to_minio(file, unique_filename)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(exc)}")

        new_doc = TaskDocument(
            task_id=task_id,
            file_name=file.filename,
            storage_path=storage_path,
            mime_type=file.content_type
        )
        db.add(new_doc)
        created_docs.append(new_doc)

    if not created_docs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun fichier valide fourni")

    db.commit()
    for doc in created_docs:
        db.refresh(doc)

    return created_docs


@router.get("/documents/{document_id}/download")
def download_task_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("tasks.read"))
):
    doc = (
        db.query(TaskDocument)
        .join(Task, TaskDocument.task_id == Task.id)
        .filter(TaskDocument.id == document_id, Task.project_id == project_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document de tâche introuvable")

    try:
        url = get_file_url_from_minio(doc.storage_path)
        return RedirectResponse(url)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable sur le stockage cloud")


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
def delete_task_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user_permissions=Depends(check_permission("tasks.update"))
):
    doc = (
        db.query(TaskDocument)
        .join(Task, TaskDocument.task_id == Task.id)
        .filter(TaskDocument.id == document_id, Task.project_id == project_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document de tâche introuvable")

    delete_file_from_minio(doc.storage_path)

    db.delete(doc)
    db.commit()

    return {"message": "Document de tâche supprimé"}

#DELETE
@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    task_id : int,
    project_id: int,
    db : Session = Depends(get_db),
    user_permissions= Depends(check_permission("tasks.delete"))
):
    task = db.query(Task).filter(Task.id==task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée dans ce projet")
    task.status=TaskStatus.ARCHIVED
    db.commit()
    return {"message": "Tâche archivée avec succès"}
