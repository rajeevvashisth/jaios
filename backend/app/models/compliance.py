from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class ComplianceObligation(Base, TimestampMixin):
    """A compliance/filing item — statutory (MCA/ROC, Income Tax, GST, state/
    local) or internal (legal, IP, contracts) — owned by Finance or Legal.

    Two independent status axes, deliberately not conflated:

    - ``applicability_status`` — do we even know this applies to us yet?
      (``applicable`` / ``not_applicable`` / ``review_pending``). Items are
      created ``review_pending`` by default; nothing should read as an
      active obligation until a human (or the Legal agent, backed by real
      facts) confirms it.
    - ``filing_status`` — where is it in the filing lifecycle (draft →
      ... → filed → completed), independent of urgency.

    ``completed``/``completed_at`` (from Phase 4) stay as the simple
    boolean/urgency-computation fields — ``services.compliance_service``
    keeps them in sync with ``filing_status`` reaching a terminal state
    (filed/completed) rather than requiring two places to update.

    ``due_date`` is nullable: an item under applicability/date review
    genuinely has no due date yet, and fabricating one would be worse than
    admitting we don't know it.
    """

    __tablename__ = "compliance_obligations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(
        String, nullable=False
    )  # tax|legal|trademark|contract|corporate|other
    owner_agent_key: Mapped[str | None] = mapped_column(
        ForeignKey("agent_definitions.agent_key"), nullable=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # none|one_time|monthly|quarterly|annual|event_based
    recurrence: Mapped[str] = mapped_column(String, default="none")
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    # e.g. "mca_roc", "income_tax", "gst", "delhi_local", "internal_legal", "other"
    jurisdiction_level: Mapped[str | None] = mapped_column(String, nullable=True)
    governing_authority: Mapped[str | None] = mapped_column(String, nullable=True)
    applicability_status: Mapped[str] = mapped_column(
        String, default="review_pending"
    )  # applicable | not_applicable | review_pending
    filing_status: Mapped[str] = mapped_column(
        String, default="draft"
    )  # draft|under_review|not_applicable|applicability_review_pending|upcoming|
    #   in_progress|awaiting_documents|awaiting_finance_input|awaiting_ca_vendor|
    #   ready_for_filing|filed|filed_proof_pending|completed|overdue
    external_owner: Mapped[str | None] = mapped_column(String, nullable=True)  # CA / vendor contact
    # [{"name": "...", "obtained": bool}, ...]
    required_documents: Mapped[list] = mapped_column(JSON, default=list)
    # {"srn": "...", "arn": "...", "challan_no": "...", "receipt_url": "...", ...}
    proof_reference: Mapped[dict] = mapped_column(JSON, default=dict)
    linked_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    # Named explicitly: mutual with finance_entries.linked_compliance_id —
    # see that column's comment for why an unnamed constraint here breaks
    # DROP ordering (CircularDependencyError) between the two tables.
    linked_expense_id: Mapped[str | None] = mapped_column(
        ForeignKey("finance_entries.id", name="fk_compliance_obligations_linked_expense_id"),
        nullable=True,
    )
