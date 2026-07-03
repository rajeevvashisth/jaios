from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="todo")  # todo|in_progress|blocked|done
    priority: Mapped[str] = mapped_column(String, default="medium")  # low|medium|high|urgent
    assignee_agent_key: Mapped[str | None] = mapped_column(
        ForeignKey("agent_definitions.agent_key"), nullable=True
    )
    assignee_human: Mapped[str | None] = mapped_column(String, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    depends_on_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
