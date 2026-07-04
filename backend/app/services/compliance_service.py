from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compliance import ComplianceObligation
from app.schemas.compliance import (
    TERMINAL_FILING_STATUSES,
    ApplicabilityStatus,
    ComplianceObligationRead,
    ComplianceObligationUpdate,
    ComplianceUrgency,
    FilingStatus,
)

DUE_SOON_WINDOW_DAYS = 14


def compute_urgency(
    obligation: ComplianceObligation, *, today: date | None = None
) -> ComplianceUrgency:
    """Derive urgency from ``due_date``/``applicability_status`` at read
    time — deliberately not a stored column, so it can never go stale
    between requests.

    ``not_applicable`` items read as ``completed`` (nothing pending) even
    though they're a distinct concept from "done" — the urgency axis only
    cares about "does this need attention right now."
    """
    if obligation.completed or obligation.applicability_status == "not_applicable":
        return ComplianceUrgency.completed
    if obligation.due_date is None:
        return ComplianceUrgency.review_pending
    today = today or date.today()
    if obligation.due_date < today:
        return ComplianceUrgency.overdue
    if obligation.due_date <= today + timedelta(days=DUE_SOON_WINDOW_DAYS):
        return ComplianceUrgency.due_soon
    return ComplianceUrgency.upcoming


def to_read(obligation: ComplianceObligation) -> ComplianceObligationRead:
    return ComplianceObligationRead(
        id=obligation.id,
        company_id=obligation.company_id,
        product_id=obligation.product_id,
        title=obligation.title,
        category=obligation.category,
        owner_agent_key=obligation.owner_agent_key,
        due_date=obligation.due_date,
        completed=obligation.completed,
        completed_at=obligation.completed_at,
        recurrence=obligation.recurrence,
        notes=obligation.notes,
        jurisdiction_level=obligation.jurisdiction_level,
        governing_authority=obligation.governing_authority,
        # Explicit enum construction (not just a str->enum annotation) so a
        # stray/legacy value stored in the DB surfaces as a clear error here
        # rather than silently passing through as a plain string.
        applicability_status=ApplicabilityStatus(obligation.applicability_status),
        filing_status=FilingStatus(obligation.filing_status),
        external_owner=obligation.external_owner,
        required_documents=obligation.required_documents,
        proof_reference=obligation.proof_reference,
        linked_task_id=obligation.linked_task_id,
        linked_expense_id=obligation.linked_expense_id,
        urgency=compute_urgency(obligation),
    )


def list_obligations(
    db: Session,
    *,
    company_id: str,
    product_id: str | None = None,
    include_completed: bool = False,
) -> list[ComplianceObligationRead]:
    stmt = select(ComplianceObligation).where(ComplianceObligation.company_id == company_id)
    if product_id:
        stmt = stmt.where(ComplianceObligation.product_id == product_id)
    if not include_completed:
        stmt = stmt.where(ComplianceObligation.completed.is_(False))
    stmt = stmt.order_by(ComplianceObligation.due_date)
    return [to_read(o) for o in db.scalars(stmt)]


def mark_completed(db: Session, *, obligation_id: str) -> ComplianceObligationRead:
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None:
        raise ValueError(f"No such compliance obligation: {obligation_id}")
    obligation.completed = True
    obligation.completed_at = datetime.now(UTC)
    obligation.filing_status = "completed"
    db.commit()
    db.refresh(obligation)
    return to_read(obligation)


def update_obligation(
    db: Session, *, obligation_id: str, updates: ComplianceObligationUpdate
) -> ComplianceObligationRead:
    """Partial update — the path for driving an obligation through its
    filing lifecycle (awaiting_documents -> ... -> filed), attaching proof
    metadata, or correcting applicability. Keeps the legacy
    ``completed``/``completed_at`` fields in sync whenever ``filing_status``
    is set to a terminal value, so ``compute_urgency`` doesn't need to know
    about filing_status at all.
    """
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None:
        raise ValueError(f"No such compliance obligation: {obligation_id}")

    data = updates.model_dump(exclude_unset=True)
    if "required_documents" in data and data["required_documents"] is not None:
        data["required_documents"] = [dict(d) for d in data["required_documents"]]

    for field, value in data.items():
        setattr(obligation, field, value)

    if updates.filing_status is not None and updates.filing_status in TERMINAL_FILING_STATUSES:
        obligation.completed = True
        obligation.completed_at = obligation.completed_at or datetime.now(UTC)

    db.commit()
    db.refresh(obligation)
    return to_read(obligation)
