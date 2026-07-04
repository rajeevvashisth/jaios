from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel


class ComplianceUrgency(StrEnum):
    completed = "completed"
    overdue = "overdue"
    due_soon = "due_soon"
    upcoming = "upcoming"
    # No due_date yet (applicability or exact date genuinely unconfirmed) —
    # distinct from "upcoming" so the UI doesn't imply a real date exists.
    review_pending = "review_pending"


class ApplicabilityStatus(StrEnum):
    applicable = "applicable"
    not_applicable = "not_applicable"
    review_pending = "review_pending"


class FilingStatus(StrEnum):
    draft = "draft"
    under_review = "under_review"
    not_applicable = "not_applicable"
    applicability_review_pending = "applicability_review_pending"
    upcoming = "upcoming"
    in_progress = "in_progress"
    awaiting_documents = "awaiting_documents"
    awaiting_finance_input = "awaiting_finance_input"
    awaiting_ca_vendor = "awaiting_ca_vendor"
    ready_for_filing = "ready_for_filing"
    filed = "filed"
    filed_proof_pending = "filed_proof_pending"
    completed = "completed"
    overdue = "overdue"


# filing_status values that mean the obligation is actually done — used to
# keep the legacy `completed`/`completed_at` fields in sync automatically.
TERMINAL_FILING_STATUSES = {FilingStatus.filed, FilingStatus.completed}


class RequiredDocument(BaseModel):
    name: str
    obtained: bool = False


class ComplianceObligationCreate(BaseModel):
    company_id: str
    product_id: str | None = None
    title: str
    category: str  # tax | legal | trademark | contract | corporate | other
    owner_agent_key: str | None = None
    due_date: date | None = None
    recurrence: str = "none"  # none | one_time | monthly | quarterly | annual | event_based
    notes: str | None = None
    jurisdiction_level: str | None = None  # mca_roc | income_tax | gst | delhi_local | ...
    governing_authority: str | None = None
    applicability_status: ApplicabilityStatus = ApplicabilityStatus.review_pending
    filing_status: FilingStatus = FilingStatus.draft
    external_owner: str | None = None
    required_documents: list[RequiredDocument] = []
    proof_reference: dict = {}
    linked_task_id: str | None = None
    linked_expense_id: str | None = None


class ComplianceObligationUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    owner_agent_key: str | None = None
    due_date: date | None = None
    recurrence: str | None = None
    notes: str | None = None
    jurisdiction_level: str | None = None
    governing_authority: str | None = None
    applicability_status: ApplicabilityStatus | None = None
    filing_status: FilingStatus | None = None
    external_owner: str | None = None
    required_documents: list[RequiredDocument] | None = None
    proof_reference: dict | None = None
    linked_task_id: str | None = None
    linked_expense_id: str | None = None


class ComplianceObligationRead(BaseModel):
    id: str
    company_id: str
    product_id: str | None
    title: str
    category: str
    owner_agent_key: str | None
    due_date: date | None
    completed: bool
    completed_at: datetime | None
    recurrence: str
    notes: str | None
    jurisdiction_level: str | None
    governing_authority: str | None
    applicability_status: ApplicabilityStatus
    filing_status: FilingStatus
    external_owner: str | None
    required_documents: list[RequiredDocument]
    proof_reference: dict
    linked_task_id: str | None
    linked_expense_id: str | None
    urgency: ComplianceUrgency
