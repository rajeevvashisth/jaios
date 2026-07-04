from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.audit import AuditLogEntry
from app.models.user import User
from app.models.workflow import WorkflowRun
from app.schemas.audit import AuditLogEntryRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogEntryRead])
def list_audit_entries(
    workflow_run_id: str | None = None,
    actor_key: str | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditLogEntry]:
    # Every audit entry today is written with a workflow_run_id (see
    # governance/audit_log.py's callers), so scoping by company means
    # joining through WorkflowRun — an entry with no workflow_run_id
    # wouldn't be attributable to any company and is excluded rather than
    # shown to everyone.
    query = (
        db.query(AuditLogEntry)
        .join(WorkflowRun, AuditLogEntry.workflow_run_id == WorkflowRun.id)
        .filter(WorkflowRun.company_id == current_user.company_id)
    )
    if workflow_run_id:
        query = query.filter(AuditLogEntry.workflow_run_id == workflow_run_id)
    if actor_key:
        query = query.filter(AuditLogEntry.actor_key == actor_key)
    return list(query.order_by(AuditLogEntry.occurred_at.desc()).limit(limit).all())
