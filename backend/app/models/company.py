from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    mission: Mapped[str | None] = mapped_column(String, nullable=True)
    strategic_goals: Mapped[list] = mapped_column(JSON, default=list)

    # Legal/jurisdiction context — drives which compliance framework applies
    # (see services/compliance_framework.py) and how finance is denominated.
    entity_type: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "LLP", "Pvt Ltd"
    country: Mapped[str] = mapped_column(String, default="India")
    jurisdiction_state: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Delhi"
    base_currency: Mapped[str] = mapped_column(String, default="INR")
