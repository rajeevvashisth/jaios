"""company jurisdiction context, product workspace path, expense detail,
richer compliance tracking

Revision ID: 0004_india_llp_extend
Revises: 0003_users
Create Date: 2026-07-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_india_llp_extend"
down_revision: Union[str, None] = "0003_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- companies: jurisdiction/entity context ---
    op.add_column("companies", sa.Column("entity_type", sa.String(), nullable=True))
    op.add_column(
        "companies",
        sa.Column("country", sa.String(), nullable=False, server_default="India"),
    )
    op.add_column("companies", sa.Column("jurisdiction_state", sa.String(), nullable=True))
    op.add_column(
        "companies",
        sa.Column("base_currency", sa.String(), nullable=False, server_default="INR"),
    )

    # --- products: local workspace path ---
    op.add_column("products", sa.Column("local_workspace_path", sa.String(), nullable=True))

    # --- finance_entries: expense detail ---
    op.add_column("finance_entries", sa.Column("subcategory", sa.String(), nullable=True))
    op.add_column("finance_entries", sa.Column("vendor", sa.String(), nullable=True))
    op.add_column(
        "finance_entries",
        sa.Column("payment_status", sa.String(), nullable=False, server_default="paid"),
    )
    op.add_column("finance_entries", sa.Column("payment_method", sa.String(), nullable=True))
    op.add_column(
        "finance_entries",
        sa.Column("proof_reference", sa.JSON(), nullable=False, server_default="{}"),
    )
    # Named explicitly (both this FK and compliance_obligations'
    # linked_expense_id below) — the two tables reference each other, and
    # an unnamed constraint leaves no DROP order SQLAlchemy/Postgres can
    # resolve automatically (CircularDependencyError on drop_all/downgrade).
    op.add_column(
        "finance_entries",
        sa.Column(
            "linked_compliance_id",
            sa.String(),
            sa.ForeignKey(
                "compliance_obligations.id", name="fk_finance_entries_linked_compliance_id"
            ),
            nullable=True,
        ),
    )

    # --- compliance_obligations: richer status model + linkage ---
    op.alter_column(
        "compliance_obligations", "due_date", existing_type=sa.Date(), nullable=True
    )
    op.add_column(
        "compliance_obligations", sa.Column("jurisdiction_level", sa.String(), nullable=True)
    )
    op.add_column(
        "compliance_obligations", sa.Column("governing_authority", sa.String(), nullable=True)
    )
    op.add_column(
        "compliance_obligations",
        sa.Column(
            "applicability_status", sa.String(), nullable=False, server_default="review_pending"
        ),
    )
    op.add_column(
        "compliance_obligations",
        sa.Column("filing_status", sa.String(), nullable=False, server_default="draft"),
    )
    op.add_column("compliance_obligations", sa.Column("external_owner", sa.String(), nullable=True))
    op.add_column(
        "compliance_obligations",
        sa.Column("required_documents", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "compliance_obligations",
        sa.Column("proof_reference", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "compliance_obligations",
        sa.Column("linked_task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=True),
    )
    op.add_column(
        "compliance_obligations",
        sa.Column(
            "linked_expense_id",
            sa.String(),
            sa.ForeignKey(
                "finance_entries.id", name="fk_compliance_obligations_linked_expense_id"
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("compliance_obligations", "linked_expense_id")
    op.drop_column("compliance_obligations", "linked_task_id")
    op.drop_column("compliance_obligations", "proof_reference")
    op.drop_column("compliance_obligations", "required_documents")
    op.drop_column("compliance_obligations", "external_owner")
    op.drop_column("compliance_obligations", "filing_status")
    op.drop_column("compliance_obligations", "applicability_status")
    op.drop_column("compliance_obligations", "governing_authority")
    op.drop_column("compliance_obligations", "jurisdiction_level")
    op.alter_column(
        "compliance_obligations", "due_date", existing_type=sa.Date(), nullable=False
    )

    op.drop_column("finance_entries", "linked_compliance_id")
    op.drop_column("finance_entries", "proof_reference")
    op.drop_column("finance_entries", "payment_method")
    op.drop_column("finance_entries", "payment_status")
    op.drop_column("finance_entries", "vendor")
    op.drop_column("finance_entries", "subcategory")

    op.drop_column("products", "local_workspace_path")

    op.drop_column("companies", "base_currency")
    op.drop_column("companies", "jurisdiction_state")
    op.drop_column("companies", "country")
    op.drop_column("companies", "entity_type")
