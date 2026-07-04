from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_own_company, require_role
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
    # Intentionally unauthenticated: a static list of graph names, not
    # tenant data — no company or user information to leak.
    return available_graphs()


@router.post("/start", response_model=WorkflowRunRead)
def start(
    payload: WorkflowStartRequest,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> WorkflowRun:
    require_own_company(current_user, payload.company_id)
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
            product_id=payload.product_id,
            workspace_path=payload.workspace_path,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[WorkflowRunRead])
def list_runs(
    company_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkflowRun]:
    if company_id:
        require_own_company(current_user, company_id)
    query = db.query(WorkflowRun).filter(WorkflowRun.company_id == current_user.company_id)
    return list(query.order_by(WorkflowRun.started_at.desc()).all())


@router.get("/{run_id}", response_model=WorkflowRunRead)
def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowRun:
    run = db.get(WorkflowRun, run_id)
    if run is None or run.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@router.get("/{run_id}/steps", response_model=list[WorkflowStepRead])
def get_run_steps(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkflowStep]:
    run = db.get(WorkflowRun, run_id)
    if run is None or run.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return list(
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_run_id == run_id)
        .order_by(WorkflowStep.step_index)
        .all()
    )


@router.get("/approvals/pending", response_model=list[ApprovalRequestRead])
def list_pending_approvals(
    company_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApprovalRequest]:
    if company_id:
        require_own_company(current_user, company_id)
    query = (
        db.query(ApprovalRequest)
        .join(WorkflowRun)
        .filter(
            ApprovalRequest.status == "pending", WorkflowRun.company_id == current_user.company_id
        )
    )
    return list(query.all())


@router.post("/{run_id}/approve", response_model=WorkflowRunRead)
def approve_or_reject(
    run_id: str,
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> WorkflowRun:
    run = db.get(WorkflowRun, run_id)
    if run is None or run.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Workflow run not found")

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
