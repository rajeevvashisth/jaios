"""users table

Revision ID: 0003_users
Revises: 0002_finance_and_compliance
Create Date: 2026-07-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_users"
down_revision: Union[str, None] = "0002_finance_and_compliance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_table("users")
