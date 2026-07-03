from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.project import Project
from app.models.task import Task
from app.models.workflow import ApprovalRequest, WorkflowRun
from app.schemas.compliance import ComplianceUrgency
from app.schemas.reports import (
    CeoSummary,
    OperationsHealth,
    ProductPortfolioEntry,
    ProductStatusReport,
    TaskStatusCounts,
)
from app.schemas.workflow import WorkflowRunRead
from app.services import compliance_service, finance_service

RECENT_RUNS_LIMIT = 10


def _task_status_counts(tasks: list[Task]) -> TaskStatusCounts:
    counts = TaskStatusCounts()
    for task in tasks:
        if hasattr(counts, task.status):
            setattr(counts, task.status, getattr(counts, task.status) + 1)
    return counts


def get_ceo_summary(db: Session, *, company_id: str) -> CeoSummary:
    """Consolidated company-wide status: portfolio, finance, operations
    health, compliance obligations, and recent workflow activity — the
    single call the Overview dashboard and a future CEO-agent narrative
    both key off of."""
    products = list(db.scalars(select(Product).where(Product.company_id == company_id)))
    all_tasks = list(db.scalars(select(Task).where(Task.company_id == company_id)))
    all_projects = list(db.scalars(select(Project).where(Project.company_id == company_id)))

    portfolio = [
        ProductPortfolioEntry(
            product_id=product.id,
            name=product.name,
            type=product.type,
            stage=product.stage,
            status=product.status,
            task_counts=_task_status_counts([t for t in all_tasks if t.product_id == product.id]),
            active_project_count=len(
                [
                    p
                    for p in all_projects
                    if p.product_id == product.id and p.status in ("planned", "active")
                ]
            ),
        )
        for product in products
    ]

    today = date.today()
    overdue_tasks = [
        t for t in all_tasks if t.due_date and t.due_date < today and t.status != "done"
    ]
    open_tasks = [t for t in all_tasks if t.status != "done"]
    blocked_tasks = [t for t in all_tasks if t.status == "blocked"]

    active_runs = list(
        db.scalars(
            select(WorkflowRun).where(
                WorkflowRun.company_id == company_id, WorkflowRun.status.in_(["running", "paused"])
            )
        )
    )
    pending_approvals = list(
        db.scalars(
            select(ApprovalRequest)
            .join(WorkflowRun, ApprovalRequest.workflow_run_id == WorkflowRun.id)
            .where(WorkflowRun.company_id == company_id, ApprovalRequest.status == "pending")
        )
    )
    recent_runs = list(
        db.scalars(
            select(WorkflowRun)
            .where(WorkflowRun.company_id == company_id)
            .order_by(WorkflowRun.started_at.desc())
            .limit(RECENT_RUNS_LIMIT)
        )
    )

    obligations = compliance_service.list_obligations(db, company_id=company_id)

    return CeoSummary(
        company_id=company_id,
        portfolio=portfolio,
        finance=finance_service.summarize_finances(db, company_id=company_id),
        operations=OperationsHealth(
            open_tasks=len(open_tasks),
            overdue_tasks=len(overdue_tasks),
            blocked_tasks=len(blocked_tasks),
            active_workflow_runs=len(active_runs),
            pending_approvals=len(pending_approvals),
        ),
        compliance_overdue=[o for o in obligations if o.urgency == ComplianceUrgency.overdue],
        compliance_due_soon=[o for o in obligations if o.urgency == ComplianceUrgency.due_soon],
        recent_workflow_runs=[WorkflowRunRead.model_validate(r) for r in recent_runs],
    )


def get_product_status_report(db: Session, *, product_id: str) -> ProductStatusReport:
    product = db.get(Product, product_id)
    if product is None:
        raise ValueError(f"No such product: {product_id}")

    tasks = list(db.scalars(select(Task).where(Task.product_id == product_id)))
    projects = list(db.scalars(select(Project).where(Project.product_id == product_id)))

    return ProductStatusReport(
        product_id=product.id,
        name=product.name,
        stage=product.stage,
        status=product.status,
        task_counts=_task_status_counts(tasks),
        project_count=len(projects),
        finance=finance_service.summarize_finances(
            db, company_id=product.company_id, product_id=product_id
        ),
        compliance_obligations=compliance_service.list_obligations(
            db, company_id=product.company_id, product_id=product_id
        ),
    )
