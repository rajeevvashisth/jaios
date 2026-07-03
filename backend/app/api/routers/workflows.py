from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.governance.approvals import decide_approval
from app.models.user import User
from app.models.workflow import ApprovalRequest, WorkflowRun, WorkflowStep
from app.orchestration.graph import available_graphs
from app.schemas.workflow import (
    ApprovalDecisionRequest,
    ApprovalRequestRead,
    WorkflowRunRead,
    WorkflowStartRequest,
    WorkflowStepRead,
)
from app.services.workflow_service import resume_workflow, start_workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/graphs")
def list_graphs() -> list[str]:
    return available_graphs()


@router.post("/start", response_model=WorkflowRunRead)
def start(payload: WorkflowStartRequest, db: Session = Depends(get_db)) -> WorkflowRun:
    goal = payload.input.get("goal", "")
    try:
        return start_workflow(
            db,
            graph_name=payload.graph_name,
            company_id=payload.company_id,
            initiating_actor=payload.initiating_actor,
            goal=goal,
            task_id=payload.task_id,
            project_id=payload.project_id,
            workspace_path=payload.workspace_path,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[WorkflowRunRead])
def list_runs(company_id: str | None = None, db: Session = Depends(get_db)) -> list[WorkflowRun]:
    query = db.query(WorkflowRun)
    if company_id:
        query = query.filter(WorkflowRun.company_id == company_id)
    return list(query.order_by(WorkflowRun.started_at.desc()).all())


@router.get("/{run_id}", response_model=WorkflowRunRead)
def get_run(run_id: str, db: Session = Depends(get_db)) -> WorkflowRun:
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@router.get("/{run_id}/steps", response_model=list[WorkflowStepRead])
def get_run_steps(run_id: str, db: Session = Depends(get_db)) -> list[WorkflowStep]:
    return list(
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_run_id == run_id)
        .order_by(WorkflowStep.step_index)
        .all()
    )


@router.get("/approvals/pending", response_model=list[ApprovalRequestRead])
def list_pending_approvals(db: Session = Depends(get_db)) -> list[ApprovalRequest]:
    return list(db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").all())


@router.post("/{run_id}/approve", response_model=WorkflowRunRead)
def approve_or_reject(
    run_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "member")),
) -> WorkflowRun:
    pending = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.workflow_run_id == run_id, ApprovalRequest.status == "pending")
        .first()
    )
    if pending is None:
        raise HTTPException(status_code=400, detail="No pending approval for this workflow run")

    decide_approval(
        db, approval_id=pending.id, decided_by=current_user.email, approve=payload.approve
    )

    try:
        return resume_workflow(db, run_id=run_id, approve=payload.approve, note=payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
