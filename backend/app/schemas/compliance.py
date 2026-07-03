from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel


class ComplianceUrgency(StrEnum):
    completed = "completed"
    overdue = "overdue"
    due_soon = "due_soon"
    upcoming = "upcoming"


class ComplianceObligationCreate(BaseModel):
    company_id: str
    product_id: str | None = None
    title: str
    category: str  # tax | legal | trademark | contract | other
    owner_agent_key: str | None = None
    due_date: date
    recurrence: str = "none"  # none | monthly | quarterly | yearly
    notes: str | None = None


class ComplianceObligationRead(BaseModel):
    id: str
    company_id: str
    product_id: str | None
    title: str
    category: str
    owner_agent_key: str | None
    due_date: date
    completed: bool
    completed_at: datetime | None
    recurrence: str
    notes: str | None
    urgency: ComplianceUrgency
