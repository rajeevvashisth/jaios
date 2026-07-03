from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    mission: str | None = None
    strategic_goals: list[str] = []


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    mission: str | None = None
    strategic_goals: list[str] | None = None


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
