from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ProjectStatus(StrEnum):
    planned = "planned"
    active = "active"
    blocked = "blocked"
    done = "done"


class ProjectBase(BaseModel):
    name: str
    goal: str | None = None
    status: ProjectStatus = ProjectStatus.planned
    start_date: date | None = None
    target_date: date | None = None


class ProjectCreate(ProjectBase):
    company_id: str
    product_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    goal: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    target_date: date | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    product_id: str | None
