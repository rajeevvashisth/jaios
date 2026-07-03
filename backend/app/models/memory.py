from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid, utcnow


class MemoryRecord(Base):
    """Structured memory, scoped by (scope_type, scope_id) + optional agent.

    ``scope_type`` is one of company|product|project|task|agent so a single
    table serves every memory scope in the spec without one table per scope.
    """

    __tablename__ = "memory_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    scope_type: Mapped[str] = mapped_column(String, nullable=False)
    scope_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_key: Mapped[str | None] = mapped_column(
        ForeignKey("agent_definitions.agent_key"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String, default="short_term")  # short_term|long_term
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
