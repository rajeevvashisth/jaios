from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    graph_name: str
    thread_id: str
    status: str
    initiating_actor: str
    company_id: str
    task_id: str | None
    project_id: str | None
    started_at: datetime
    completed_at: datetime | None


class WorkflowStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_run_id: str
    agent_key: str
    step_index: int
    input: dict
    output: dict
    status: str
    started_at: datetime
    completed_at: datetime | None


class WorkflowStartRequest(BaseModel):
    graph_name: str
    company_id: str
    task_id: str | None = None
    project_id: str | None = None
    product_id: str | None = None
    initiating_actor: str = "human"
    # If omitted, resolved from product_id (directly, or via task_id/
    # project_id's product) -> Product.local_workspace_path. See
    # services/workflow_service.py's _resolve_workspace_path.
    workspace_path: str | None = None
    input: dict = {}


class ApprovalDecisionRequest(BaseModel):
    """``decided_by`` is deliberately absent — the deciding identity comes
    from the authenticated caller (``current_user.email``), never from the
    request body, so it can't be spoofed by whoever holds the API key."""

    approve: bool
    note: str | None = None


class ApprovalRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_run_id: str
    workflow_step_id: str | None
    action_type: str
    requested_by_agent_key: str
    summary: str
    status: str
    decided_by: str | None
    decided_at: datetime | None
    created_at: datetime
