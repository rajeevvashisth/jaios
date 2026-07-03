from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogEntryCreate(BaseModel):
    actor_type: str  # agent|human|system
    actor_key: str
    action: str
    target_type: str | None = None
    target_id: str | None = None
    tool_used: str | None = None
    input: dict = {}
    output: dict = {}
    workflow_run_id: str | None = None


class AuditLogEntryRead(AuditLogEntryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    occurred_at: datetime
