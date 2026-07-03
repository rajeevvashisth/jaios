from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class User(Base, TimestampMixin):
    """A human account. Every user belongs to exactly one company —
    multi-tenant-per-user (one login across several companies) is out of
    scope until there's a real second tenant to design against.

    ``role`` is a coarse floor, not the agent permission model: agents'
    tool/approval boundaries are governed by ``AgentSpec``
    (agents/types.py), unrelated to this. ``admin`` can decide approvals and
    manage users; ``member`` can decide approvals but not manage users;
    ``viewer`` can read but not decide anything.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="member")  # admin | member | viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
