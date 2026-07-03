from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.finance import FinanceEntry
from app.schemas.finance import FinanceEntryCreate, FinanceEntryRead, FinanceSummary
from app.services.finance_service import summarize_finances

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/entries", response_model=FinanceEntryRead)
def create_entry(payload: FinanceEntryCreate, db: Session = Depends(get_db)) -> FinanceEntry:
    entry = FinanceEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/entries", response_model=list[FinanceEntryRead])
def list_entries(
    company_id: str,
    product_id: str | None = None,
    entry_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[FinanceEntry]:
    query = db.query(FinanceEntry).filter(FinanceEntry.company_id == company_id)
    if product_id:
        query = query.filter(FinanceEntry.product_id == product_id)
    if entry_type:
        query = query.filter(FinanceEntry.entry_type == entry_type)
    return list(query.order_by(FinanceEntry.occurred_on.desc()).all())


@router.get("/summary", response_model=FinanceSummary)
def get_summary(
    company_id: str,
    product_id: str | None = None,
    since: date | None = None,
    until: date | None = None,
    db: Session = Depends(get_db),
) -> FinanceSummary:
    return summarize_finances(
        db, company_id=company_id, product_id=product_id, since=since, until=until
    )
