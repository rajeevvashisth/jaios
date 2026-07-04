from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIUsageRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    provider: str
    model: str
    task_type: str
    agent_key: str | None
    tokens_in: int | None
    tokens_out: int | None
    workflow_run_id: str | None
    occurred_at: datetime


class AIUsageSummary(BaseModel):
    workspace_id: str
    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    calls_by_provider: dict[str, int]
    calls_by_task_type: dict[str, int]
