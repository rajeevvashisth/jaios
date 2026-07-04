from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_own_company, require_role
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_routing import route_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead)
def create_task(
    payload: TaskCreate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> Task:
    require_own_company(current_user, payload.company_id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    if company_id:
        require_own_company(current_user, company_id)
    query = db.query(Task).filter(Task.company_id == current_user.company_id)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if product_id:
        query = query.filter(Task.product_id == product_id)
    if status:
        query = query.filter(Task.status == status)
    return list(query.all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/route", response_model=TaskRead)
def route_task_endpoint(
    task_id: str,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> Task:
    """Auto-assign the task to the best-fit agent via keyword routing."""
    task = db.get(Task, task_id)
    if task is None or task.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return route_task(db, task)
