"""finance entries and compliance obligations

Revision ID: 0002_finance_and_compliance
Revises: 0001_initial_schema
Create Date: 2026-07-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_finance_and_compliance"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "finance_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("is_recurring", sa.Boolean(), nullable=False),
        sa.Column("recurrence_interval", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_finance_entries_company_product",
        "finance_entries",
        ["company_id", "product_id"],
    )

    op.create_table(
        "compliance_obligations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column(
            "owner_agent_key",
            sa.String(),
            sa.ForeignKey("agent_definitions.agent_key"),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_compliance_obligations_company_due_date",
        "compliance_obligations",
        ["company_id", "due_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_compliance_obligations_company_due_date", table_name="compliance_obligations")
    op.drop_table("compliance_obligations")
    op.drop_index("ix_finance_entries_company_product", table_name="finance_entries")
    op.drop_table("finance_entries")
