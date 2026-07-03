from app.orchestration.graph import available_graphs
from app.orchestration.specialized_nodes import MAX_QA_RETRIES, route_after_qa
from app.orchestration.state import merge_dicts
from app.orchestration.workflows.incident_response import route_incident


def test_available_graphs_includes_all_five_reference_workflows():
    graphs = available_graphs()
    assert set(graphs) == {
        "task_delegation",
        "portfolio_review",
        "compliance_review",
        "revenue_cost_review",
        "incident_response",
    }


def test_all_graphs_compile_against_a_real_checkpointer(_engine):
    """Regression test for a real bug: compiling any graph triggers
    ``get_checkpointer()``, whose one-time ``setup()`` runs
    ``CREATE INDEX CONCURRENTLY`` — which blocks until every other open
    transaction finishes. A live Docker Compose run surfaced a self-deadlock
    where a request's own idle-in-transaction session (left open by
    ``db.refresh()`` in ``start_workflow``) blocked that very setup() call
    forever. Fixed by calling ``get_checkpointer()`` eagerly at app startup
    (main.py) and by committing before invoking any graph
    (workflow_service.py) — this test only proves compilation itself still
    works, not the concurrency scenario, which needs a live server to
    reproduce.
    """
    from app.orchestration.graph import available_graphs, get_graph

    for name in available_graphs():
        assert get_graph(name) is not None


def test_route_incident_defaults_to_developer_fix():
    state = {"goal": "Checkout API is throwing 500s in production", "context": {}}
    assert route_incident(state) == "developer_fix"


def test_route_incident_routes_to_qa_on_regression_signal():
    state = {
        "goal": "Investigate incident",
        "context": {"cto": {"response": "This looks like a flaky regression in the test suite."}},
    }
    assert route_incident(state) == "qa_verify"


def test_route_incident_reads_goal_text_too():
    state = {"goal": "Existing test for checkout is failing intermittently", "context": {}}
    assert route_incident(state) == "qa_verify"


def test_merge_dicts_keeps_prior_agent_outputs():
    current = {"ceo": {"response": "prioritize X"}}
    update = {"cto": {"response": "plan for X"}}
    merged = merge_dicts(current, update)
    assert merged == {"ceo": {"response": "prioritize X"}, "cto": {"response": "plan for X"}}


def test_merge_dicts_does_not_mutate_input():
    current = {"ceo": {"response": "a"}}
    merge_dicts(current, {"cto": {"response": "b"}})
    assert current == {"ceo": {"response": "a"}}


def test_route_after_qa_proceeds_to_devops_when_tests_pass():
    state = {"context": {"qa": {"tests_failed": 0}}, "qa_retry_count": 0}
    assert route_after_qa(state) == "devops"


def test_route_after_qa_reworks_on_failure_within_retry_budget():
    state = {"context": {"qa": {"tests_failed": 1}}, "qa_retry_count": 1}
    assert route_after_qa(state) == "developer_rework"


def test_route_after_qa_gives_up_after_max_retries():
    state = {
        "context": {"qa": {"tests_failed": 1}},
        "qa_retry_count": MAX_QA_RETRIES + 1,
    }
    assert route_after_qa(state) == "devops"
