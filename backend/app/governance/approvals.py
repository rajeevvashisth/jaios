from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.agents.registry import agent_registry
from app.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import approval_decisions_total
from app.models.workflow import ApprovalRequest

logger = get_logger(__name__)


def action_requires_approval(agent_key: str, action_type: str) -> bool:
    """An action needs human sign-off if either the agent's own spec flags it
    (e.g. DevOps + 'deploy') or it's in the company-wide global list — the
    global list is a floor that can't be relaxed per-agent."""
    settings = get_settings()
    if action_type in settings.global_approval_required_action_list:
        return True
    spec = agent_registry.get(agent_key)
    return action_type in spec.requires_approval_for


def create_approval_request(
    db: Session,
    *,
    workflow_run_id: str,
    action_type: str,
    requested_by_agent_key: str,
    summary: str,
    workflow_step_id: str | None = None,
) -> ApprovalRequest:
    req = ApprovalRequest(
        workflow_run_id=workflow_run_id,
        workflow_step_id=workflow_step_id,
        action_type=action_type,
        requested_by_agent_key=requested_by_agent_key,
        summary=summary,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def decide_approval(
    db: Session, *, approval_id: str, decided_by: str, approve: bool
) -> ApprovalRequest:
    req = db.get(ApprovalRequest, approval_id)
    if req is None:
        raise ValueError(f"No such approval request: {approval_id}")
    if req.status != "pending":
        raise ValueError(f"Approval request {approval_id} already decided: {req.status}")

    req.status = "approved" if approve else "rejected"
    req.decided_by = decided_by
    req.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(req)

    approval_decisions_total.labels(action_type=req.action_type, decision=req.status).inc()
    logger.info(
        "approval_decided",
        approval_id=approval_id,
        action_type=req.action_type,
        decision=req.status,
        decided_by=decided_by,
    )
    return req
