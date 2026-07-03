from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class TaskStatus(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"


class TaskPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    assignee_agent_key: str | None = None
    assignee_human: str | None = None
    due_date: date | None = None
    depends_on_task_id: str | None = None


class TaskCreate(TaskBase):
    company_id: str
    project_id: str | None = None
    product_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_agent_key: str | None = None
    assignee_human: str | None = None
    due_date: date | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str | None
    product_id: str | None
