from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid, utcnow


class AuditLogEntry(Base):
    """Append-only record of every agent decision and tool call.

    Never updated after insert — this is the record relied on for
    auditability and incident review, so mutation would defeat its purpose.
    """

    __tablename__ = "audit_log_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)  # agent|human|system
    actor_key: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String, nullable=True)
    target_id: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_used: Mapped[str | None] = mapped_column(String, nullable=True)
    input: Mapped[dict] = mapped_column(JSON, default=dict)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    workflow_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=True
    )
