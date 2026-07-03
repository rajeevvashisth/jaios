from types import SimpleNamespace

from app.models.company import Company
from app.models.workflow import WorkflowRun, WorkflowStep
from app.orchestration.specialized_nodes import build_developer_node, build_qa_node


def _fake_llm(monkeypatch, text: str) -> None:
    class FakeChatModel:
        def invoke(self, messages):
            return SimpleNamespace(content=text)

    monkeypatch.setattr("app.orchestration.nodes.get_chat_model", lambda *a, **kw: FakeChatModel())


def _make_run_id(db_session, name: str) -> str:
    """Returns the new run's id as a plain string — callers hold onto the
    ORM object only long enough to commit it. The specialized node closes
    its own DB session (which, in these tests, monkeypatches to the shared
    ``db_session`` fixture), which would otherwise leave any ORM object we
    kept around detached and unusable for follow-up assertions."""
    company = Company(name=name)
    db_session.add(company)
    db_session.commit()
    run = WorkflowRun(graph_name="task_delegation", initiating_actor="test", company_id=company.id)
    db_session.add(run)
    db_session.commit()
    return run.id


def test_developer_node_invokes_coding_worker_and_records_step(db_session, tmp_path, monkeypatch):
    _fake_llm(monkeypatch, "Implementation plan: add endpoint")
    monkeypatch.setattr("app.orchestration.specialized_nodes.SessionLocal", lambda: db_session)
    run_id = _make_run_id(db_session, "Developer Node Co")

    node = build_developer_node()
    result = node(
        {
            "workflow_run_id": run_id,
            "goal": "Add endpoint",
            "context": {},
            "workspace_path": str(tmp_path),
        }
    )

    developer_output = result["context"]["developer"]
    assert developer_output["response"] == "Implementation plan: add endpoint"
    # No `claude` CLI in this environment — the worker degrades gracefully
    # rather than the node crashing, and that failure is recorded truthfully.
    assert developer_output["coding_worker_success"] is False
    assert developer_output["coding_worker_backend"] == "claude_code"

    steps = db_session.query(WorkflowStep).filter(WorkflowStep.workflow_run_id == run_id).all()
    assert len(steps) == 1
    assert steps[0].agent_key == "developer"
    assert steps[0].status == "completed"


def test_qa_node_runs_real_tests_and_increments_retry_on_failure(db_session, tmp_path, monkeypatch):
    _fake_llm(monkeypatch, "Test plan: run pytest")
    monkeypatch.setattr("app.orchestration.specialized_nodes.SessionLocal", lambda: db_session)
    (tmp_path / "test_sample.py").write_text("def test_fail():\n    assert False\n")
    run_id = _make_run_id(db_session, "QA Node Co Failing")

    node = build_qa_node()
    result = node(
        {
            "workflow_run_id": run_id,
            "goal": "verify fix",
            "context": {},
            "workspace_path": str(tmp_path),
            "qa_retry_count": 0,
        }
    )

    assert result["context"]["qa"]["tests_failed"] == 1
    assert result["qa_retry_count"] == 1


def test_qa_node_does_not_increment_retry_on_pass(db_session, tmp_path, monkeypatch):
    _fake_llm(monkeypatch, "Test plan: run pytest")
    monkeypatch.setattr("app.orchestration.specialized_nodes.SessionLocal", lambda: db_session)
    (tmp_path / "test_sample.py").write_text("def test_ok():\n    assert True\n")
    run_id = _make_run_id(db_session, "QA Node Co Passing")

    node = build_qa_node()
    result = node(
        {
            "workflow_run_id": run_id,
            "goal": "verify fix",
            "context": {},
            "workspace_path": str(tmp_path),
            "qa_retry_count": 0,
        }
    )

    assert result["context"]["qa"]["tests_failed"] == 0
    assert result["qa_retry_count"] == 0
