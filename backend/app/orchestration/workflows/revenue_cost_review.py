"""Reference workflow: Finance -> CEO.

Matches spec Example Workflow 4 (revenue/cost review). This is a reporting
workflow — nothing is spent or committed, so unlike ``compliance_review`` it
has no approval checkpoint.
"""

from langgraph.graph import END, START, StateGraph

from app.orchestration.checkpoints import get_checkpointer
from app.orchestration.nodes import build_agent_node
from app.orchestration.state import WorkflowState


def build_revenue_cost_review_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("finance_summary", build_agent_node("finance"))
    graph.add_node("ceo_review", build_agent_node("ceo"))

    graph.add_edge(START, "finance_summary")
    graph.add_edge("finance_summary", "ceo_review")
    graph.add_edge("ceo_review", END)

    return graph.compile(checkpointer=get_checkpointer())
