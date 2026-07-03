from typing import Any

from sqlalchemy.orm import Session

from app.agents.registry import agent_registry
from app.core.logging import get_logger
from app.core.metrics import tool_calls_total
from app.governance import audit_log
from app.tools.base import ToolResult
from app.tools.registry import tool_registry

logger = get_logger(__name__)


class ToolPermissionError(PermissionError):
    pass


def check_tool_permission(agent_key: str, tool_key: str) -> None:
    spec = agent_registry.get(agent_key)
    if tool_key not in spec.allowed_tools:
        raise ToolPermissionError(f"Agent '{agent_key}' is not permitted to use tool '{tool_key}'")


def invoke_tool_for_agent(
    db: Session,
    *,
    agent_key: str,
    tool_key: str,
    action: str,
    workflow_run_id: str | None = None,
    **kwargs: Any,
) -> ToolResult:
    """The only path through which an agent should ever touch a tool.

    Checks the agent's ``allowed_tools`` from its :class:`AgentSpec`, invokes
    the tool, and writes an audit log entry regardless of outcome — so a
    denied or failed call is just as visible in the audit trail as a
    successful one. Also increments ``jaios_tool_calls_total`` (denied vs.
    failure vs. success) so a spike in denials or failures shows up in
    metrics without having to mine the audit log.
    """
    try:
        check_tool_permission(agent_key, tool_key)
    except ToolPermissionError:
        tool_calls_total.labels(tool_key=tool_key, outcome="denied").inc()
        logger.warning("tool_call_denied", agent_key=agent_key, tool_key=tool_key, action=action)
        raise

    tool = tool_registry.get(tool_key)
    result = tool.run(action, **kwargs)

    tool_calls_total.labels(
        tool_key=tool_key, outcome="success" if result.success else "failure"
    ).inc()
    logger.info(
        "tool_call",
        agent_key=agent_key,
        tool_key=tool_key,
        action=action,
        success=result.success,
        workflow_run_id=workflow_run_id,
    )

    audit_log.record(
        db,
        actor_type="agent",
        actor_key=agent_key,
        action=action,
        target_type="tool",
        target_id=tool_key,
        tool_used=tool_key,
        input={k: v for k, v in kwargs.items() if k != "db"},
        output=result.model_dump(),
        workflow_run_id=workflow_run_id,
    )
    return result
