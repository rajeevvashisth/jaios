from enum import StrEnum

from pydantic import BaseModel


class AgentLayer(StrEnum):
    executive = "executive"
    technology = "technology"
    governance = "governance"


class MemoryScope(StrEnum):
    company = "company"
    product = "product"
    project = "project"
    agent_private = "agent_private"


class AgentSpec(BaseModel):
    """Static, git-versioned definition of an agent's behavior and boundaries.

    This is the source of truth for what an agent is allowed to do. Runtime
    state (enabled/disabled, config overrides, last activity) lives in the
    ``agent_definitions`` DB table, keyed by the same ``key``.
    """

    key: str
    name: str
    layer: AgentLayer
    responsibility: str
    system_prompt: str
    allowed_tools: list[str] = []
    memory_scope: MemoryScope = MemoryScope.company
    can_delegate_to: list[str] = []
    requires_approval_for: list[str] = []
    escalates_to: str | None = None
