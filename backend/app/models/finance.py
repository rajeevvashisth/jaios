from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class FinanceEntry(Base, TimestampMixin):
    """A single revenue or expense line, optionally attached to a product.

    Amounts are stored as integer minor units (``amount_cents`` — cents,
    paise, etc.) rather than float, so aggregation never accumulates
    floating-point rounding error. Phase 4 assumes a single operating
    currency per company (no FX conversion) — a known simplification, not
    an oversight; see docs/architecture.md.
    """

    __tablename__ = "finance_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    entry_type: Mapped[str] = mapped_column(String, nullable=False)  # revenue | expense
    category: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="INR")
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_interval: Mapped[str | None] = mapped_column(String, nullable=True)
