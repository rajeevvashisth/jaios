from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compliance import ComplianceObligation
from app.schemas.compliance import ComplianceObligationRead, ComplianceUrgency

DUE_SOON_WINDOW_DAYS = 14


def compute_urgency(
    obligation: ComplianceObligation, *, today: date | None = None
) -> ComplianceUrgency:
    """Derive urgency from ``due_date`` at read time — deliberately not a
    stored column, so it can never go stale between requests."""
    if obligation.completed:
        return ComplianceUrgency.completed
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
    db.commit()
    db.refresh(obligation)
    return to_read(obligation)
