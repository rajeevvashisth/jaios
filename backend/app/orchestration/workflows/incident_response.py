"""Reference workflow: DevOps -> CTO -> {Developer | QA} -> CEO status update.

Matches spec Example Workflow 5 (incident / deployment support), and is the
reference pattern for *conditional* routing based on an upstream agent's
output — unlike ``task_delegation`` (linear) and ``portfolio_review``
(static fan-out/fan-in), the path after CTO's triage depends on what CTO
actually said.
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.orchestration.checkpoints import get_checkpointer
from app.orchestration.nodes import build_agent_node
from app.orchestration.specialized_nodes import build_developer_node, build_qa_node
from app.orchestration.state import WorkflowState

_QA_SIGNAL_KEYWORDS = ("regression", "flaky", "test failure", "existing test", "already fixed")


def route_incident(state: WorkflowState) -> str:
    """Route to QA when the incident reads as a test/regression problem
    (i.e. the code is likely fine and the issue is in verification); default
    to Developer otherwise, since most incidents are an actual code/infra
    bug needing a fix rather than a re-verification.
    """
    context: dict[str, Any] = state.get("context", {})
    cto_output = str(context.get("cto", {}).get("response", "")).lower()
    goal = str(state.get("goal") or "").lower()
    combined = f"{goal} {cto_output}"
    if any(keyword in combined for keyword in _QA_SIGNAL_KEYWORDS):
        return "qa_verify"
    return "developer_fix"


def build_incident_response_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("devops_triage", build_agent_node("devops"))
    graph.add_node("cto", build_agent_node("cto"))
    graph.add_node("developer_fix", build_developer_node())
    graph.add_node("qa_verify", build_qa_node())
    graph.add_node("ceo_status_update", build_agent_node("ceo"))

    graph.add_edge(START, "devops_triage")
    graph.add_edge("devops_triage", "cto")
    graph.add_conditional_edges(
        "cto", route_incident, {"developer_fix": "developer_fix", "qa_verify": "qa_verify"}
    )
    graph.add_edge("developer_fix", "ceo_status_update")
    graph.add_edge("qa_verify", "ceo_status_update")
    graph.add_edge("ceo_status_update", END)

    return graph.compile(checkpointer=get_checkpointer())
