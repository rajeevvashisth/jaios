from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class ComplianceObligation(Base, TimestampMixin):
    """A due-date-bound obligation — tax filing, trademark renewal, contract
    renewal, policy review — owned by Finance or Legal.

    Urgency (upcoming/due_soon/overdue) is deliberately NOT a stored column:
    it's derived from ``due_date`` at read time (see
    ``services.compliance_service``) so it can't go stale between requests.
    Only ``completed`` is persisted, since that's a real user action.
    """

    __tablename__ = "compliance_obligations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(
        String, nullable=False
    )  # tax|legal|trademark|contract|other
    owner_agent_key: Mapped[str | None] = mapped_column(
        ForeignKey("agent_definitions.agent_key"), nullable=True
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recurrence: Mapped[str] = mapped_column(String, default="none")  # none|monthly|quarterly|yearly
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
