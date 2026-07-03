from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class FinanceEntryType(StrEnum):
    revenue = "revenue"
    expense = "expense"


class FinanceEntryCreate(BaseModel):
    company_id: str
    product_id: str | None = None
    entry_type: FinanceEntryType
    category: str
    amount_cents: int
    currency: str = "INR"
    description: str | None = None
    occurred_on: date
    is_recurring: bool = False
    recurrence_interval: str | None = None


class FinanceEntryRead(FinanceEntryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


class CategoryBreakdown(BaseModel):
    category: str
    amount_cents: int


class FinanceSummary(BaseModel):
    company_id: str
    product_id: str | None
    currency: str
    revenue_cents: int
    expense_cents: int
    margin_cents: int
    revenue_by_category: list[CategoryBreakdown]
    expense_by_category: list[CategoryBreakdown]
