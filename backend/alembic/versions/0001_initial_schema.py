"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "companies",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("mission", sa.String(), nullable=True),
        sa.Column("strategic_goals", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "agent_definitions",
        sa.Column("agent_key", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("layer", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("owner", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("roadmap", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("goal", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column(
            "assignee_agent_key",
            sa.String(),
            sa.ForeignKey("agent_definitions.agent_key"),
            nullable=True,
        ),
        sa.Column("assignee_human", sa.String(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("depends_on_task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("graph_name", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("initiating_actor", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "workflow_run_id", sa.String(), sa.ForeignKey("workflow_runs.id"), nullable=False
        ),
        sa.Column("agent_key", sa.String(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "workflow_run_id", sa.String(), sa.ForeignKey("workflow_runs.id"), nullable=False
        ),
        sa.Column(
            "workflow_step_id", sa.String(), sa.ForeignKey("workflow_steps.id"), nullable=True
        ),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("requested_by_agent_key", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "memory_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.Column(
            "agent_key", sa.String(), sa.ForeignKey("agent_definitions.agent_key"), nullable=True
        ),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_memory_records_scope", "memory_records", ["scope_type", "scope_id"]
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_uri", sa.String(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "document_id", sa.String(), sa.ForeignKey("knowledge_documents.id"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("chunk_metadata", sa.JSON(), nullable=False),
    )

    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("actor_key", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("tool_used", sa.String(), nullable=True),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column(
            "workflow_run_id", sa.String(), sa.ForeignKey("workflow_runs.id"), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log_entries")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_memory_records_scope", table_name="memory_records")
    op.drop_table("memory_records")
    op.drop_table("approval_requests")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_runs")
    op.drop_table("tasks")
    op.drop_table("projects")
    op.drop_table("products")
    op.drop_table("agent_definitions")
    op.drop_table("companies")
