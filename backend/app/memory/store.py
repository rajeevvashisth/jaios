from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import MemoryRecord


def write_memory(
    db: Session,
    *,
    scope_type: str,
    scope_id: str,
    content: dict[str, Any],
    kind: str = "short_term",
    agent_key: str | None = None,
    expires_at: datetime | None = None,
) -> MemoryRecord:
    record = MemoryRecord(
        scope_type=scope_type,
        scope_id=scope_id,
        agent_key=agent_key,
        kind=kind,
        content=content,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_memory(
    db: Session,
    *,
    scope_type: str,
    scope_id: str,
    agent_key: str | None = None,
    kind: str | None = None,
    limit: int = 50,
) -> list[MemoryRecord]:
    stmt = (
        select(MemoryRecord)
        .where(MemoryRecord.scope_type == scope_type, MemoryRecord.scope_id == scope_id)
        .order_by(MemoryRecord.created_at.desc())
        .limit(limit)
    )
    if agent_key is not None:
        stmt = stmt.where(MemoryRecord.agent_key == agent_key)
    if kind is not None:
        stmt = stmt.where(MemoryRecord.kind == kind)
    return list(db.scalars(stmt))
