from typing import Any

from langgraph.types import interrupt
from sqlalchemy.orm import Session

from app.agents.registry import agent_registry
from app.core.llm_provider import LLMMessage, get_chat_model
from app.core.logging import get_logger
from app.core.metrics import agent_turns_total
from app.db.session import SessionLocal
from app.governance import audit_log
from app.governance.approvals import action_requires_approval, create_approval_request
from app.models.workflow import WorkflowStep
from app.orchestration.state import WorkflowState

logger = get_logger(__name__)


def plan_with_llm(agent_key: str, state: WorkflowState) -> str:
    """Call the agent's LLM with its system prompt + the workflow goal +
    prior agents' outputs. Shared by the generic node builder and the
    specialized Developer/QA nodes, which follow this call with an actual
    tool invocation rather than treating the LLM's text as the final word.
    """
    spec = agent_registry.get(agent_key)
    messages = [
        LLMMessage(role="system", content=spec.system_prompt),
        LLMMessage(
            role="user",
            content=(
                f"Company goal / task: {state.get('goal')}\n\n"
                f"Prior agent outputs so far: {state.get('context', {})}\n\n"
                f"Produce your output as {spec.name}. Be specific and concise."
            ),
        ),
    ]
    return get_chat_model().invoke(messages).content


def record_step(
    db: Session, state: WorkflowState, agent_key: str, output: dict[str, Any]
) -> WorkflowStep:
    """Persist a completed ``WorkflowStep`` + matching audit log entry."""
    step = WorkflowStep(
        workflow_run_id=state["workflow_run_id"],
        agent_key=agent_key,
        step_index=len(state.get("context", {})),
        input={"goal": state.get("goal"), "context": state.get("context", {})},
        output=output,
        status="completed",
    )
    db.add(step)
    db.commit()
    db.refresh(step)

    audit_log.record(
        db,
        actor_type="agent",
        actor_key=agent_key,
        action="agent_turn",
        target_type="workflow_run",
        target_id=state["workflow_run_id"],
        input={"goal": state.get("goal")},
        output=output,
        workflow_run_id=state["workflow_run_id"],
    )

    agent_turns_total.labels(agent_key=agent_key).inc()
    logger.info("agent_turn", agent_key=agent_key, workflow_run_id=state["workflow_run_id"])

    return step


def build_agent_node(agent_key: str, action_type: str | None = None):
    """Build a LangGraph node function for one agent.

    Each call: (1) if ``action_type`` requires approval for this agent,
    raises a LangGraph ``interrupt`` and waits for a human decision recorded
    via an ``ApprovalRequest`` row; (2) otherwise calls the LLM and records a
    ``WorkflowStep`` + audit log entry. Agents that actually drive a tool
    (Developer, QA) use the specialized node builders in
    ``specialized_nodes.py`` instead of this generic one.
    """
    spec = agent_registry.get(agent_key)

    def node(state: WorkflowState) -> dict[str, Any]:
        db = SessionLocal()
        try:
            if action_type and action_requires_approval(agent_key, action_type):
                approval = create_approval_request(
                    db,
                    workflow_run_id=state["workflow_run_id"],
                    action_type=action_type,
                    requested_by_agent_key=agent_key,
                    summary=f"{spec.name} requests approval for action '{action_type}'",
                )
                logger.info(
                    "approval_requested",
                    agent_key=agent_key,
                    action_type=action_type,
                    approval_id=approval.id,
                    workflow_run_id=state["workflow_run_id"],
                )
                decision = interrupt(
                    {
                        "approval_id": approval.id,
                        "agent_key": agent_key,
                        "action_type": action_type,
                    }
                )
                if not decision.get("approve"):
                    return {
                        "status": "rejected",
                        "context": {
                            agent_key: {"decision": "rejected", "note": decision.get("note")}
                        },
                    }

            response_text = plan_with_llm(agent_key, state)
            output = {"response": response_text}
            record_step(db, state, agent_key, output)

            return {"context": {agent_key: output}}
        finally:
            db.close()

    return node
