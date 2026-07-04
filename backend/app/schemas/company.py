from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    mission: str | None = None
    strategic_goals: list[str] = []
    entity_type: str | None = None
    country: str = "India"
    jurisdiction_state: str | None = None
    base_currency: str = "INR"


class CompanyCreate(CompanyBase):
    # Omit to bootstrap a brand new workspace named after this company
    # (the pre-workspace behavior). Pass the id of an existing workspace
    # to add a second company to it — only allowed for an authenticated
    # user who already belongs to that workspace (see companies.py).
    workspace_id: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    mission: str | None = None
    strategic_goals: list[str] | None = None
    entity_type: str | None = None
    country: str | None = None
    jurisdiction_state: str | None = None
    base_currency: str | None = None


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
