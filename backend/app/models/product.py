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
