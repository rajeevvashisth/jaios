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
from app.models.company import Company
from app.models.workflow import WorkflowStep
from app.orchestration.state import WorkflowState
from app.services import ai_usage_service, model_router

logger = get_logger(__name__)

# Maps each agent to the routing task_type that best describes its work —
# see services/model_router.py for how task_type drives provider/model
# choice. Agents not listed default to "general_chat" (local tier).
AGENT_TASK_TYPE: dict[str, str] = {
    "ceo": "company_planning",
    "cto": "product_feature_planning",
    "developer": "coding_assistance",
    "qa": "coding_assistance",
    "devops": "coding_assistance",
    "finance": "finance_summary",
    "legal": "compliance_summary",
    "operations": "workflow_followup_draft",
}


def _resolve_workspace_id(db: Session, company_id: str | None) -> str | None:
    if not company_id:
        return None
    company = db.get(Company, company_id)
    return company.workspace_id if company else None


def plan_with_llm(agent_key: str, state: WorkflowState, db: Session) -> str:
    """Call the agent's LLM with its system prompt + the workflow goal +
    prior agents' outputs. Shared by the generic node builder and the
    specialized Developer/QA nodes, which follow this call with an actual
    tool invocation rather than treating the LLM's text as the final word.

    Routes the call through ``model_router`` (task type -> provider/model,
    honoring the workspace's configured BYOK providers and operating mode)
    and logs a best-effort usage record — a failure logging usage must
    never break the agent turn itself.
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

    task_type = AGENT_TASK_TYPE.get(agent_key, "general_chat")
    workspace_id = _resolve_workspace_id(db, state.get("company_id"))
    decision = model_router.route(
        db, workspace_id=workspace_id, task_type=task_type, agent_key=agent_key
    )

    response = get_chat_model(
        decision.provider, decision.model, api_key=decision.api_key, base_url=decision.base_url
    ).invoke(messages)

    try:
        usage = (response.raw or {}).get("usage", {}) if response.raw else {}
        ai_usage_service.record_usage(
            db,
            workspace_id=workspace_id,
            provider=response.provider,
            model=response.model,
            task_type=task_type,
            agent_key=agent_key,
            tokens_in=usage.get("input_tokens") or usage.get("prompt_tokens"),
            tokens_out=usage.get("output_tokens") or usage.get("completion_tokens"),
            workflow_run_id=state.get("workflow_run_id"),
        )
    except Exception:  # noqa: BLE001 — usage logging must never break the agent turn
        logger.warning("ai_usage_log_failed", agent_key=agent_key, task_type=task_type)

    return response.content


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

            response_text = plan_with_llm(agent_key, state, db)
            output = {"response": response_text}
            record_step(db, state, agent_key, output)

            return {"context": {agent_key: output}}
        finally:
            db.close()

    return node
