from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_routing import route_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    company_id: str | None = None,
    project_id: str | None = None,
    product_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Task]:
    query = db.query(Task)
    if company_id:
        query = query.filter(Task.company_id == company_id)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if product_id:
        query = query.filter(Task.product_id == product_id)
    if status:
        query = query.filter(Task.status == status)
    return list(query.all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/route", response_model=TaskRead)
def route_task_endpoint(task_id: str, db: Session = Depends(get_db)) -> Task:
    """Auto-assign the task to the best-fit agent via keyword routing."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return route_task(db, task)
