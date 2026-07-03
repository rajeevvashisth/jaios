"""Reference workflow: CEO -> CTO -> Developer -> QA -> DevOps -> CEO review.

Matches spec Example Workflow 1 (new product feature delivery). DevOps'
deploy step is the human-in-the-loop checkpoint — everything upstream of it
runs unattended. QA runs the real test suite (not just an LLM opinion) and
loops back to Developer on genuine failures, up to a bounded retry count,
before proceeding to DevOps regardless.
"""

from langgraph.graph import END, START, StateGraph

from app.orchestration.checkpoints import get_checkpointer
from app.orchestration.nodes import build_agent_node
from app.orchestration.specialized_nodes import build_developer_node, build_qa_node, route_after_qa
from app.orchestration.state import WorkflowState


def build_task_delegation_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("ceo_kickoff", build_agent_node("ceo"))
    graph.add_node("cto", build_agent_node("cto"))
    graph.add_node("developer", build_developer_node())
    graph.add_node("qa", build_qa_node())
    graph.add_node("devops", build_agent_node("devops", action_type="deploy"))
    graph.add_node("ceo_review", build_agent_node("ceo"))

    graph.add_edge(START, "ceo_kickoff")
    graph.add_edge("ceo_kickoff", "cto")
    graph.add_edge("cto", "developer")
    graph.add_edge("developer", "qa")
    graph.add_conditional_edges(
        "qa", route_after_qa, {"developer_rework": "developer", "devops": "devops"}
    )
    graph.add_edge("devops", "ceo_review")
    graph.add_edge("ceo_review", END)

    return graph.compile(checkpointer=get_checkpointer())
