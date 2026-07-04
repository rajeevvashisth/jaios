from datetime import date

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class FinanceEntry(Base, TimestampMixin):
    """A single revenue, expense, or capital-contribution line, optionally
    attached to a product.

    Amounts are stored as integer minor units (``amount_cents`` — cents,
    paise, etc.) rather than float, so aggregation never accumulates
    floating-point rounding error. Assumes a single operating currency per
    company (no FX conversion) — a known simplification, not an oversight;
    see docs/architecture.md.

    ``vendor``/``payment_status``/``payment_method``/``proof_reference`` are
    nullable and mostly meaningful for expenses — a revenue or capital entry
    just leaves them unset rather than needing a separate table.
    """

    __tablename__ = "finance_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    entry_type: Mapped[str] = mapped_column(String, nullable=False)  # revenue | expense | capital
    category: Mapped[str] = mapped_column(String, nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="INR")
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_interval: Mapped[str | None] = mapped_column(String, nullable=True)

    vendor: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_status: Mapped[str] = mapped_column(
        String, default="paid"
    )  # paid | unpaid | partially_paid | reimbursable
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True)
    # Free-form metadata blob: invoice number, receipt URL, challan/reference
    # number — deliberately JSON rather than named columns since proof
    # formats vary a lot by category and this isn't queried structurally.
    proof_reference: Mapped[dict] = mapped_column(JSON, default=dict)
    # Named explicitly: this FK and compliance_obligations.linked_expense_id
    # form a mutual reference between the two tables, and an unnamed
    # constraint leaves SQLAlchemy/Postgres unable to pick a DROP order for
    # either table (CircularDependencyError) — naming it lets DROP use
    # ALTER TABLE ... DROP CONSTRAINT to break the cycle first.
    linked_compliance_id: Mapped[str | None] = mapped_column(
        ForeignKey("compliance_obligations.id", name="fk_finance_entries_linked_compliance_id"),
        nullable=True,
    )
