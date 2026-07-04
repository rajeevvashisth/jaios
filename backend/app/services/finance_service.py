from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import FinanceEntry
from app.schemas.finance import CategoryBreakdown, FinanceEntryUpdate, FinanceSummary


def summarize_finances(
    db: Session,
    *,
    company_id: str,
    product_id: str | None = None,
    since: date | None = None,
    until: date | None = None,
) -> FinanceSummary:
    """Aggregate revenue/expense/margin for a company, optionally scoped to
    one product and/or a date range.

    Assumes a single operating currency per company — no FX conversion is
    attempted. Mixed-currency entries are summed together as a known
    simplification (see FinanceEntry's docstring), not silently dropped.
    """
    stmt = select(FinanceEntry).where(FinanceEntry.company_id == company_id)
    if product_id:
        stmt = stmt.where(FinanceEntry.product_id == product_id)
    if since:
        stmt = stmt.where(FinanceEntry.occurred_on >= since)
    if until:
        stmt = stmt.where(FinanceEntry.occurred_on <= until)

    entries = list(db.scalars(stmt))
    currency = entries[0].currency if entries else "INR"

    buckets: dict[str, dict[str, int]] = {"revenue": {}, "expense": {}, "capital": {}}
    for entry in entries:
        bucket = buckets.get(entry.entry_type, buckets["expense"])
        bucket[entry.category] = bucket.get(entry.category, 0) + entry.amount_cents

    revenue_cents = sum(buckets["revenue"].values())
    expense_cents = sum(buckets["expense"].values())
    capital_cents = sum(buckets["capital"].values())

    return FinanceSummary(
        company_id=company_id,
        product_id=product_id,
        currency=currency,
        revenue_cents=revenue_cents,
        expense_cents=expense_cents,
        # Margin is strictly P&L (revenue - expense) — capital contributions
        # are equity, not income, and must never inflate it.
        margin_cents=revenue_cents - expense_cents,
        capital_cents=capital_cents,
        revenue_by_category=[
            CategoryBreakdown(category=k, amount_cents=v)
            for k, v in sorted(buckets["revenue"].items())
        ],
        expense_by_category=[
            CategoryBreakdown(category=k, amount_cents=v)
            for k, v in sorted(buckets["expense"].items())
        ],
        capital_by_category=[
            CategoryBreakdown(category=k, amount_cents=v)
            for k, v in sorted(buckets["capital"].items())
        ],
    )


def update_entry(db: Session, *, entry_id: str, updates: FinanceEntryUpdate) -> FinanceEntry:
    """Partial update — mainly for correcting a placeholder value (e.g. an
    entry recorded with an approximate date) or transitioning
    ``payment_status`` as a bill actually gets paid."""
    entry = db.get(FinanceEntry, entry_id)
    if entry is None:
        raise ValueError(f"No such finance entry: {entry_id}")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry
