from datetime import date, timedelta

import pytest

from app.models.compliance import ComplianceObligation
from app.models.finance import FinanceEntry
from app.models.product import Product
from app.models.project import Project
from app.models.task import Task
from app.models.workflow import ApprovalRequest, WorkflowRun
from app.services.reports_service import get_ceo_summary, get_product_status_report


def test_ceo_summary_aggregates_portfolio_finance_ops_and_compliance(db_session, make_company):
    company = make_company("Reports Co")

    product = Product(company_id=company.id, name="Flagship", stage="live", status="active")
    db_session.add(product)
    db_session.commit()

    db_session.add(
        Project(company_id=company.id, product_id=product.id, name="Q3 push", status="active")
    )
    db_session.add_all(
        [
            Task(company_id=company.id, product_id=product.id, title="Todo one", status="todo"),
            Task(
                company_id=company.id,
                product_id=product.id,
                title="Overdue one",
                status="in_progress",
                due_date=date.today() - timedelta(days=2),
            ),
            Task(
                company_id=company.id, product_id=product.id, title="Blocked one", status="blocked"
            ),
            Task(company_id=company.id, product_id=product.id, title="Done one", status="done"),
        ]
    )
    db_session.add(
        FinanceEntry(
            company_id=company.id,
            product_id=product.id,
            entry_type="revenue",
            category="subscriptions",
            amount_cents=1000_00,
            occurred_on=date.today(),
        )
    )
    db_session.add(
        ComplianceObligation(
            company_id=company.id,
            title="Overdue filing",
            category="tax",
            due_date=date.today() - timedelta(days=1),
        )
    )
    run = WorkflowRun(
        graph_name="task_delegation",
        initiating_actor="test",
        company_id=company.id,
        status="paused",
    )
    db_session.add(run)
    db_session.commit()
    db_session.add(
        ApprovalRequest(
            workflow_run_id=run.id,
            action_type="deploy",
            requested_by_agent_key="devops",
            summary="Deploy to prod",
        )
    )
    db_session.commit()

    summary = get_ceo_summary(db_session, company_id=company.id)

    assert len(summary.portfolio) == 1
    portfolio_entry = summary.portfolio[0]
    assert portfolio_entry.task_counts.todo == 1
    assert portfolio_entry.task_counts.in_progress == 1
    assert portfolio_entry.task_counts.blocked == 1
    assert portfolio_entry.task_counts.done == 1
    assert portfolio_entry.active_project_count == 1

    assert summary.finance.revenue_cents == 1000_00
    assert summary.operations.open_tasks == 3
    assert summary.operations.overdue_tasks == 1
    assert summary.operations.blocked_tasks == 1
    assert summary.operations.active_workflow_runs == 1
    assert summary.operations.pending_approvals == 1
    assert len(summary.compliance_overdue) == 1
    assert len(summary.recent_workflow_runs) == 1


def test_product_status_report(db_session, make_company):
    company = make_company("Product Report Co")

    product = Product(company_id=company.id, name="Widget", stage="building")
    db_session.add(product)
    db_session.commit()

    db_session.add(
        Task(company_id=company.id, product_id=product.id, title="Build it", status="todo")
    )
    db_session.add(Project(company_id=company.id, product_id=product.id, name="Widget v1"))
    db_session.add(
        FinanceEntry(
            company_id=company.id,
            product_id=product.id,
            entry_type="expense",
            category="infra",
            amount_cents=50_00,
            occurred_on=date.today(),
        )
    )
    db_session.commit()

    report = get_product_status_report(db_session, product_id=product.id)
    assert report.name == "Widget"
    assert report.task_counts.todo == 1
    assert report.project_count == 1
    assert report.finance.expense_cents == 50_00


def test_product_status_report_raises_for_unknown_product(db_session):
    with pytest.raises(ValueError):
        get_product_status_report(db_session, product_id="not-a-real-id")
