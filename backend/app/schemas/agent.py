from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_key: str
    name: str
    layer: str
    enabled: bool
    config: dict
    last_active_at: datetime | None = None


class AgentDefinitionUpdate(BaseModel):
    enabled: bool | None = None
    config: dict | None = None


class AgentSpecRead(BaseModel):
    """Static spec info merged with DB runtime state, returned by the API."""

    key: str
    name: str
    layer: str
    responsibility: str
    allowed_tools: list[str]
    memory_scope: str
    can_delegate_to: list[str]
    requires_approval_for: list[str]
    escalates_to: str | None
    enabled: bool
    last_active_at: datetime | None = None
