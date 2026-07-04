"""workspaces (multi-tenant top-level), AI provider config (BYOK), AI usage tracking

Revision ID: 0005_workspace_ai_provider
Revises: 0004_india_llp_extend
Create Date: 2026-07-04
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_workspace_ai_provider"
down_revision: Union[str, None] = "0004_india_llp_extend"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("operating_mode", sa.String(), nullable=False, server_default="balanced"),
        sa.Column("monthly_budget_cents", sa.Integer(), nullable=True),
        sa.Column("daily_budget_cents", sa.Integer(), nullable=True),
        sa.Column("ask_before_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column("companies", sa.Column("workspace_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_companies_workspace_id", "companies", "workspaces", ["workspace_id"], ["id"]
    )

    # Backfill: every pre-existing company (including the real Jyka Labs
    # LLP row) gets its own new workspace named after it — "one workspace
    # per company" is the only safe default for data that predates the
    # workspace concept; grouping unrelated companies together would be a
    # guess this migration has no basis for making.
    bind = op.get_bind()
    workspaces_table = sa.table(
        "workspaces",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("operating_mode", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    companies_table = sa.table(
        "companies",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("workspace_id", sa.String()),
    )
    now = sa.func.now()
    existing_companies = bind.execute(
        sa.select(companies_table.c.id, companies_table.c.name)
    ).fetchall()
    for company_id, company_name in existing_companies:
        workspace_id = str(uuid.uuid4())
        bind.execute(
            workspaces_table.insert().values(
                id=workspace_id,
                name=f"{company_name} Workspace",
                operating_mode="balanced",
                created_at=now,
                updated_at=now,
            )
        )
        bind.execute(
            companies_table.update()
            .where(companies_table.c.id == company_id)
            .values(workspace_id=workspace_id)
        )

    op.alter_column("companies", "workspace_id", existing_type=sa.String(), nullable=False)

    op.create_table(
        "ai_provider_configs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=False
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ai_usage_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=False
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("agent_key", sa.String(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column(
            "workflow_run_id", sa.String(), sa.ForeignKey("workflow_runs.id"), nullable=True
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_usage_records")
    op.drop_table("ai_provider_configs")
    op.drop_constraint("fk_companies_workspace_id", "companies", type_="foreignkey")
    op.drop_column("companies", "workspace_id")
    op.drop_table("workspaces")
