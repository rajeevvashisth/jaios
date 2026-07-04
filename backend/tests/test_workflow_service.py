from app.models.company import Company
from app.models.product import Product
from app.models.project import Project
from app.models.task import Task
from app.services.workflow_service import _resolve_workspace_path


def _make_company_and_product(db_session, name: str, workspace_path: str | None):
    company = Company(name=name)
    db_session.add(company)
    db_session.commit()
    product = Product(
        company_id=company.id, name=f"{name} Product", local_workspace_path=workspace_path
    )
    db_session.add(product)
    db_session.commit()
    return company, product


def test_explicit_workspace_path_always_wins(db_session):
    _, product = _make_company_and_product(db_session, "Explicit Co", "/products/stored-path")

    resolved = _resolve_workspace_path(
        db_session,
        explicit="/explicit/override",
        product_id=product.id,
        task_id=None,
        project_id=None,
    )
    assert resolved == "/explicit/override"


def test_resolves_from_direct_product_id(db_session):
    _, product = _make_company_and_product(db_session, "Direct Product Co", "/products/thandimandi")

    resolved = _resolve_workspace_path(
        db_session, explicit=None, product_id=product.id, task_id=None, project_id=None
    )
    assert resolved == "/products/thandimandi"


def test_resolves_via_task_product(db_session):
    company, product = _make_company_and_product(
        db_session, "Task Product Co", "/products/via-task"
    )
    task = Task(company_id=company.id, product_id=product.id, title="Ship feature")
    db_session.add(task)
    db_session.commit()

    resolved = _resolve_workspace_path(
        db_session, explicit=None, product_id=None, task_id=task.id, project_id=None
    )
    assert resolved == "/products/via-task"


def test_resolves_via_project_product(db_session):
    company, product = _make_company_and_product(
        db_session, "Project Product Co", "/products/via-project"
    )
    project = Project(company_id=company.id, product_id=product.id, name="Q3 push")
    db_session.add(project)
    db_session.commit()

    resolved = _resolve_workspace_path(
        db_session, explicit=None, product_id=None, task_id=None, project_id=project.id
    )
    assert resolved == "/products/via-project"


def test_returns_none_when_nothing_resolves(db_session):
    resolved = _resolve_workspace_path(
        db_session, explicit=None, product_id=None, task_id=None, project_id=None
    )
    assert resolved is None


def test_returns_none_when_product_has_no_workspace_path(db_session):
    _, product = _make_company_and_product(db_session, "No Path Co", None)

    resolved = _resolve_workspace_path(
        db_session, explicit=None, product_id=product.id, task_id=None, project_id=None
    )
    assert resolved is None
