from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Workspace(Base, TimestampMixin):
    """The top-level tenant boundary. A workspace can own one or more
    companies (e.g. a holding structure, or a founder running several
    ventures) plus workspace-wide AI provider configuration and usage
    policy — those are workspace-scoped, not company-scoped, since a BYOK
    key or an Ollama endpoint is typically shared infrastructure for
    whoever is running the workspace, not duplicated per company.

    Deliberately no separate membership table yet: each ``User`` still
    belongs to exactly one ``Company`` (see ``models/user.py``), and a
    user's "own workspace" is resolved through that company. Multi-company
    membership per user is real future work, not needed for v1.
    """

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Operating mode drives default model-routing tier preference (see
    # services/model_router.py) — "balanced" respects each task's natural
    # tier, the others force every task to one tier regardless of type.
    operating_mode: Mapped[str] = mapped_column(String, default="balanced")
    # balanced | lowest_cost | highest_quality | privacy_first

    # Soft caps only — v1 tracks and displays usage against these but does
    # not hard-block requests. Null means "no budget set."
    monthly_budget_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_budget_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ask_before_premium: Mapped[bool] = mapped_column(Boolean, default=False)
