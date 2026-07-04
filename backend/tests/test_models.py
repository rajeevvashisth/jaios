from app.models.product import Product
from app.models.project import Project
from app.models.task import Task


def test_company_product_project_task_hierarchy_persists(db_session, make_company):
    company = make_company("Jyka Labs", mission="Run an AI-native company")

    product = Product(company_id=company.id, name="Thandimandi", type="saas", stage="live")
    db_session.add(product)
    db_session.commit()

    project = Project(company_id=company.id, product_id=product.id, name="Q3 growth push")
    db_session.add(project)
    db_session.commit()

    task = Task(
        company_id=company.id,
        project_id=project.id,
        product_id=product.id,
        title="Ship pricing page",
        status="todo",
        priority="high",
    )
    db_session.add(task)
    db_session.commit()

    fetched = db_session.get(Task, task.id)
    assert fetched.title == "Ship pricing page"
    assert fetched.project_id == project.id
    assert fetched.product_id == product.id
    assert fetched.company_id == company.id


def test_task_can_depend_on_another_task(db_session, make_company):
    company = make_company("Jyka Labs 2")

    first = Task(company_id=company.id, title="Design schema", status="done")
    db_session.add(first)
    db_session.commit()

    second = Task(
        company_id=company.id,
        title="Build API on schema",
        depends_on_task_id=first.id,
    )
    db_session.add(second)
    db_session.commit()

    fetched = db_session.get(Task, second.id)
    assert fetched.depends_on_task_id == first.id
