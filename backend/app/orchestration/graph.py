from collections.abc import Callable

from app.orchestration.workflows.compliance_review import build_compliance_review_graph
from app.orchestration.workflows.incident_response import build_incident_response_graph
from app.orchestration.workflows.portfolio_review import build_portfolio_review_graph
from app.orchestration.workflows.revenue_cost_review import build_revenue_cost_review_graph
from app.orchestration.workflows.task_delegation import build_task_delegation_graph

GRAPH_BUILDERS: dict[str, Callable] = {
    "task_delegation": build_task_delegation_graph,
    "portfolio_review": build_portfolio_review_graph,
    "compliance_review": build_compliance_review_graph,
    "revenue_cost_review": build_revenue_cost_review_graph,
    "incident_response": build_incident_response_graph,
}

_compiled_cache: dict[str, object] = {}


def get_graph(graph_name: str):
    """Return the compiled graph for ``graph_name``, building (and caching)
    it on first use. New workflows register here — one entry, no other
    wiring required."""
    if graph_name not in GRAPH_BUILDERS:
        raise KeyError(f"Unknown workflow graph: {graph_name}")
    if graph_name not in _compiled_cache:
        _compiled_cache[graph_name] = GRAPH_BUILDERS[graph_name]()
    return _compiled_cache[graph_name]


def available_graphs() -> list[str]:
    return list(GRAPH_BUILDERS.keys())
