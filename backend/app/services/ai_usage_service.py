from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.ai_usage import AIUsageRecord
from app.schemas.ai_usage import AIUsageRecordRead, AIUsageSummary

logger = get_logger(__name__)


def record_usage(
    db: Session,
    *,
    workspace_id: str | None,
    provider: str,
    model: str,
    task_type: str,
    agent_key: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    workflow_run_id: str | None = None,
) -> None:
    """Best-effort usage logging — a failure here must never break the
    agent turn it's recording, so callers should wrap this in try/except
    (see orchestration/nodes.py)."""
    if workspace_id is None:
        return
    db.add(
        AIUsageRecord(
            workspace_id=workspace_id,
            provider=provider,
            model=model,
            task_type=task_type,
            agent_key=agent_key,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            workflow_run_id=workflow_run_id,
        )
    )
    db.commit()


def list_usage(db: Session, *, workspace_id: str, limit: int = 200) -> list[AIUsageRecordRead]:
    rows = (
        db.query(AIUsageRecord)
        .filter(AIUsageRecord.workspace_id == workspace_id)
        .order_by(AIUsageRecord.occurred_at.desc())
        .limit(limit)
        .all()
    )
    return [AIUsageRecordRead.model_validate(r) for r in rows]


def summarize_usage(db: Session, *, workspace_id: str) -> AIUsageSummary:
    rows = db.query(AIUsageRecord).filter(AIUsageRecord.workspace_id == workspace_id).all()
    calls_by_provider: dict[str, int] = {}
    calls_by_task_type: dict[str, int] = {}
    tokens_in = 0
    tokens_out = 0
    for row in rows:
        calls_by_provider[row.provider] = calls_by_provider.get(row.provider, 0) + 1
        calls_by_task_type[row.task_type] = calls_by_task_type.get(row.task_type, 0) + 1
        tokens_in += row.tokens_in or 0
        tokens_out += row.tokens_out or 0
    return AIUsageSummary(
        workspace_id=workspace_id,
        total_calls=len(rows),
        total_tokens_in=tokens_in,
        total_tokens_out=tokens_out,
        calls_by_provider=calls_by_provider,
        calls_by_task_type=calls_by_task_type,
    )
