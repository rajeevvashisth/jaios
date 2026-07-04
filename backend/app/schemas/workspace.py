from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class OperatingMode(StrEnum):
    balanced = "balanced"
    lowest_cost = "lowest_cost"
    highest_quality = "highest_quality"
    privacy_first = "privacy_first"


class WorkspaceCreate(BaseModel):
    name: str
    operating_mode: OperatingMode = OperatingMode.balanced


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    operating_mode: OperatingMode | None = None
    monthly_budget_cents: int | None = None
    daily_budget_cents: int | None = None
    ask_before_premium: bool | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    operating_mode: OperatingMode
    monthly_budget_cents: int | None
    daily_budget_cents: int | None
    ask_before_premium: bool
