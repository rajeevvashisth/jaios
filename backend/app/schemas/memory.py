from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class MemoryScopeType(StrEnum):
    company = "company"
    product = "product"
    project = "project"
    task = "task"
    agent = "agent"


class MemoryKind(StrEnum):
    short_term = "short_term"
    long_term = "long_term"


class MemoryRecordCreate(BaseModel):
    scope_type: MemoryScopeType
    scope_id: str
    agent_key: str | None = None
    kind: MemoryKind = MemoryKind.short_term
    content: dict
    expires_at: datetime | None = None


class MemoryRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scope_type: str
    scope_id: str
    agent_key: str | None
    kind: str
    content: dict
    created_at: datetime
    expires_at: datetime | None
