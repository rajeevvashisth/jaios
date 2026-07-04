from app.models.task import Task
from app.services.task_routing import route_task, suggest_agent_for_task


def test_suggest_agent_matches_devops_keywords():
    task = Task(title="Deploy new release to production", company_id="x")
    assert suggest_agent_for_task(task) == "devops"


def test_suggest_agent_matches_qa_keywords():
    task = Task(title="Investigate flaky regression test in checkout suite", company_id="x")
    assert suggest_agent_for_task(task) == "qa"


def test_suggest_agent_matches_legal_keywords():
    task = Task(title="Review NDA and trademark filing", company_id="x")
    assert suggest_agent_for_task(task) == "legal"


def test_suggest_agent_matches_finance_keywords():
    task = Task(title="Reconcile vendor invoice and update budget", company_id="x")
    assert suggest_agent_for_task(task) == "finance"


def test_suggest_agent_falls_back_to_operations_when_no_keywords_match():
    task = Task(title="asdf qwerty", company_id="x")
    assert suggest_agent_for_task(task) == "operations"


def test_route_task_persists_assignee(db_session, make_company):
    company = make_company("Routing Co")

    task = Task(company_id=company.id, title="Fix Docker build pipeline")
    db_session.add(task)
    db_session.commit()

    routed = route_task(db_session, task)
    assert routed.assignee_agent_key == "devops"

    fetched = db_session.get(Task, task.id)
    assert fetched.assignee_agent_key == "devops"
