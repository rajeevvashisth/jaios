from pydantic import BaseModel

from app.schemas.compliance import ComplianceObligationRead
from app.schemas.finance import FinanceSummary
from app.schemas.workflow import WorkflowRunRead


class TaskStatusCounts(BaseModel):
    todo: int = 0
    in_progress: int = 0
    blocked: int = 0
    done: int = 0


class ProductPortfolioEntry(BaseModel):
    product_id: str
    name: str
    type: str
    stage: str
    status: str
    task_counts: TaskStatusCounts
    active_project_count: int


class OperationsHealth(BaseModel):
    open_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    active_workflow_runs: int
    pending_approvals: int


class CeoSummary(BaseModel):
    company_id: str
    portfolio: list[ProductPortfolioEntry]
    finance: FinanceSummary
    operations: OperationsHealth
    compliance_overdue: list[ComplianceObligationRead]
    compliance_due_soon: list[ComplianceObligationRead]
    recent_workflow_runs: list[WorkflowRunRead]


class ProductStatusReport(BaseModel):
    product_id: str
    name: str
    stage: str
    status: str
    task_counts: TaskStatusCounts
    project_count: int
    finance: FinanceSummary
    compliance_obligations: list[ComplianceObligationRead]
