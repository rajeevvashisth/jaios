from langgraph.types import Command
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import workflow_runs_total
from app.db.base import utcnow
from app.models.workflow import WorkflowRun
from app.orchestration.graph import get_graph
from app.orchestration.state import WorkflowState

logger = get_logger(__name__)


def _apply_post_invoke_status(run: WorkflowRun, result: dict, *, rejected: bool = False) -> None:
    interrupted = bool(result.get("__interrupt__"))
    if interrupted:
        run.status = "paused"
    elif rejected or result.get("status") == "rejected":
        run.status = "failed"
        run.completed_at = utcnow()
    else:
        run.status = "completed"
        run.completed_at = utcnow()

    if run.status in ("completed", "failed"):
        workflow_runs_total.labels(graph_name=run.graph_name, status=run.status).inc()
        logger.info(
            "workflow_run_finished", graph_name=run.graph_name, status=run.status, run_id=run.id
        )


def start_workflow(
    db: Session,
    *,
    graph_name: str,
    company_id: str,
    initiating_actor: str,
    goal: str,
    task_id: str | None = None,
    project_id: str | None = None,
    workspace_path: str | None = None,
) -> WorkflowRun:
    """Create a WorkflowRun row and drive the named graph to completion or
    its first approval checkpoint."""
    run = WorkflowRun(
        graph_name=graph_name,
        status="running",
        initiating_actor=initiating_actor,
        company_id=company_id,
        task_id=task_id,
        project_id=project_id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    # graph.invoke() below can run for the duration of several LLM calls.
    # Commit again here (a no-op on data, since nothing changed since the
    # line above) purely to close the transaction db.refresh() opened —
    # otherwise this session sits idle-in-transaction on the request's own
    # connection for the entire run, which is at best a wasted pool slot and
    # at worst (the first time any graph is compiled) a self-deadlock against
    # the checkpointer's one-time CREATE INDEX CONCURRENTLY setup.
    db.commit()

    graph = get_graph(graph_name)
    config = {"configurable": {"thread_id": run.thread_id}}
    initial_state: WorkflowState = {
        "company_id": company_id,
        "workflow_run_id": run.id,
        "originating_task_id": task_id,
        "goal": goal,
        "workspace_path": workspace_path,
        "context": {},
        "qa_retry_count": 0,
        "status": "running",
    }
    result = graph.invoke(initial_state, config=config)

    _apply_post_invoke_status(run, result)
    db.commit()
    db.refresh(run)
    return run


def resume_workflow(
    db: Session, *, run_id: str, approve: bool, note: str | None = None
) -> WorkflowRun:
    """Resume a paused (approval-interrupted) workflow run with a human
    decision. Rejecting an approval fails the run rather than continuing —
    callers that want a retry path should start a new workflow run."""
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise ValueError(f"No such workflow run: {run_id}")
    if run.status != "paused":
        raise ValueError(f"Workflow run {run_id} is not paused (status={run.status})")
    db.commit()  # close the read transaction before the (potentially long) invoke below

    graph = get_graph(run.graph_name)
    config = {"configurable": {"thread_id": run.thread_id}}
    result = graph.invoke(Command(resume={"approve": approve, "note": note}), config=config)

    _apply_post_invoke_status(run, result, rejected=not approve)
    db.commit()
    db.refresh(run)
    return run
