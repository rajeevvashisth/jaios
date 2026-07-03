from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ProductType(StrEnum):
    saas = "saas"
    platform = "platform"
    internal_tool = "internal_tool"
    ai_product = "ai_product"
    other = "other"


class ProductStage(StrEnum):
    idea = "idea"
    building = "building"
    live = "live"
    sunset = "sunset"


class ProductBase(BaseModel):
    name: str
    type: ProductType = ProductType.saas
    stage: ProductStage = ProductStage.idea
    owner: str | None = None
    status: str = "active"
    description: str | None = None
    roadmap: list[str] = []


class ProductCreate(ProductBase):
    company_id: str


class ProductUpdate(BaseModel):
    name: str | None = None
    type: ProductType | None = None
    stage: ProductStage | None = None
    owner: str | None = None
    status: str | None = None
    description: str | None = None
    roadmap: list[str] | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
