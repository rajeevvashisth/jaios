"""Reference workflow: CEO fan-out to Finance + Operations + CTO, then a
consolidated CEO report. Matches spec Example Workflow 2 (product
prioritization review). Demonstrates the fan-out/fan-in shape other
cross-functional reviews (e.g. revenue/cost review) can copy.
"""

from langgraph.graph import END, START, StateGraph

from app.orchestration.checkpoints import get_checkpointer
from app.orchestration.nodes import build_agent_node
from app.orchestration.state import WorkflowState


def build_portfolio_review_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("ceo_kickoff", build_agent_node("ceo"))
    graph.add_node("finance", build_agent_node("finance"))
    graph.add_node("operations", build_agent_node("operations"))
    graph.add_node("cto", build_agent_node("cto"))
    graph.add_node("ceo_consolidate", build_agent_node("ceo"))

    graph.add_edge(START, "ceo_kickoff")
    graph.add_edge("ceo_kickoff", "finance")
    graph.add_edge("ceo_kickoff", "operations")
    graph.add_edge("ceo_kickoff", "cto")
    graph.add_edge("finance", "ceo_consolidate")
    graph.add_edge("operations", "ceo_consolidate")
    graph.add_edge("cto", "ceo_consolidate")
    graph.add_edge("ceo_consolidate", END)

    return graph.compile(checkpointer=get_checkpointer())
