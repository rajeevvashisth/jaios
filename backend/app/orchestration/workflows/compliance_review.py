"""Reference workflow: Legal -> Operations -> CEO notify.

Matches spec Example Workflow 3 (compliance reminder / legal review). The
Legal node's action type is ``legal_signature`` so any run that reaches it
pauses for human sign-off before the obligation is handed to Operations for
tracking — Legal never finalizes a binding action unattended.
"""

from langgraph.graph import END, START, StateGraph

from app.orchestration.checkpoints import get_checkpointer
from app.orchestration.nodes import build_agent_node
from app.orchestration.state import WorkflowState


def build_compliance_review_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("legal_review", build_agent_node("legal", action_type="legal_signature"))
    graph.add_node("operations_followup", build_agent_node("operations"))
    graph.add_node("ceo_notify", build_agent_node("ceo"))

    graph.add_edge(START, "legal_review")
    graph.add_edge("legal_review", "operations_followup")
    graph.add_edge("operations_followup", "ceo_notify")
    graph.add_edge("ceo_notify", END)

    return graph.compile(checkpointer=get_checkpointer())
