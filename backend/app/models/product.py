from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Product(Base, TimestampMixin):
    """A product / business unit in the company's portfolio."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(
        String, default="saas"
    )  # saas|platform|internal_tool|ai_product|other
    stage: Mapped[str] = mapped_column(String, default="idea")  # idea|building|live|sunset
    owner: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    roadmap: Mapped[list] = mapped_column(JSON, default=list)

    # The product's local codebase, if any — Developer/QA/DevOps agents use
    # this as the default `workspace_path` for workflow runs scoped to this
    # product (see services/workflow_service.py), so a task/workflow tied to
    # this product operates on the real repo without it having to be typed
    # in every time. A single path, not a repo table: one product maps to
    # one primary local workspace today; revisit if that stops being true.
    local_workspace_path: Mapped[str | None] = mapped_column(String, nullable=True)
