from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    # Every company belongs to exactly one workspace (the tenant boundary
    # — see models/workspace.py). The migration backfills a new workspace
    # per pre-existing company before this column was added, so it's
    # non-nullable from the ORM's perspective even though the underlying
    # column started nullable during that one-time migration.
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    mission: Mapped[str | None] = mapped_column(String, nullable=True)
    strategic_goals: Mapped[list] = mapped_column(JSON, default=list)

    # Legal/jurisdiction context — drives which compliance framework applies
    # (see services/compliance_framework.py) and how finance is denominated.
    entity_type: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "LLP", "Pvt Ltd"
    country: Mapped[str] = mapped_column(String, default="India")
    jurisdiction_state: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Delhi"
    base_currency: Mapped[str] = mapped_column(String, default="INR")
