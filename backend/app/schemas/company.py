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
    pass


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
