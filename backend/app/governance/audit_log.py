from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLogEntry


def record(
    db: Session,
    *,
    actor_type: str,
    actor_key: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    tool_used: str | None = None,
    input: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    workflow_run_id: str | None = None,
) -> AuditLogEntry:
    """Write one append-only audit entry. Every agent decision and tool call
    must go through here — it is the sole source of truth for "what did the
    system do and why" during an incident review."""
    entry = AuditLogEntry(
        actor_type=actor_type,
        actor_key=actor_key,
        action=action,
        target_type=target_type,
        target_id=target_id,
        tool_used=tool_used,
        input=input or {},
        output=output or {},
        workflow_run_id=workflow_run_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
