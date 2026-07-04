from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid, utcnow


class AIUsageRecord(Base):
    """One row per LLM call, for the usage/cost visibility surface.

    Token counts are best-effort: Anthropic/OpenAI responses report usage
    and populate both fields; Ollama's chat API does not reliably return
    token counts, so those rows are logged with ``tokens_in``/``tokens_out``
    left null rather than a fabricated estimate. Never updated after
    insert, same reasoning as ``AuditLogEntry``.
    """

    __tablename__ = "ai_usage_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    agent_key: Mapped[str | None] = mapped_column(String, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workflow_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
