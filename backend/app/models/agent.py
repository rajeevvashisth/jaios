from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AgentDefinition(Base, TimestampMixin):
    """Runtime state for an agent whose behavior spec lives in code.

    The authoritative prompt/tools/rules live in ``app.agents.definitions``
    (git-versioned). This row only tracks what the UI/ops need to change at
    runtime without a code deploy: enabled flag, config overrides, and last
    activity for observability.
    """

    __tablename__ = "agent_definitions"

    agent_key: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    layer: Mapped[str] = mapped_column(String, nullable=False)  # executive|technology|governance
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
