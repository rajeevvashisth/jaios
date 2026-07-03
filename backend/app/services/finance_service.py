from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import FinanceEntry
from app.schemas.finance import CategoryBreakdown, FinanceSummary


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

    revenue_by_category: dict[str, int] = {}
    expense_by_category: dict[str, int] = {}
    for entry in entries:
        bucket = revenue_by_category if entry.entry_type == "revenue" else expense_by_category
        bucket[entry.category] = bucket.get(entry.category, 0) + entry.amount_cents

    revenue_cents = sum(revenue_by_category.values())
    expense_cents = sum(expense_by_category.values())

    return FinanceSummary(
        company_id=company_id,
        product_id=product_id,
        currency=currency,
        revenue_cents=revenue_cents,
        expense_cents=expense_cents,
        margin_cents=revenue_cents - expense_cents,
        revenue_by_category=[
            CategoryBreakdown(category=k, amount_cents=v)
            for k, v in sorted(revenue_by_category.items())
        ],
        expense_by_category=[
            CategoryBreakdown(category=k, amount_cents=v)
            for k, v in sorted(expense_by_category.items())
        ],
    )
