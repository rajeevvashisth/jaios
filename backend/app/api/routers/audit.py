from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audit import AuditLogEntry
from app.schemas.audit import AuditLogEntryRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogEntryRead])
def list_audit_entries(
    workflow_run_id: str | None = None,
    actor_key: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[AuditLogEntry]:
    query = db.query(AuditLogEntry)
    if workflow_run_id:
        query = query.filter(AuditLogEntry.workflow_run_id == workflow_run_id)
    if actor_key:
        query = query.filter(AuditLogEntry.actor_key == actor_key)
    return list(query.order_by(AuditLogEntry.occurred_at.desc()).limit(limit).all())
