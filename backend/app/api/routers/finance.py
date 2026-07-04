from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_own_company, require_role
from app.models.finance import FinanceEntry
from app.models.user import User
from app.schemas.finance import (
    FinanceEntryCreate,
    FinanceEntryRead,
    FinanceEntryUpdate,
    FinanceSummary,
)
from app.services.finance_service import summarize_finances, update_entry

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("/entries", response_model=FinanceEntryRead)
def create_entry(
    payload: FinanceEntryCreate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> FinanceEntry:
    require_own_company(current_user, payload.company_id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FinanceEntry]:
    require_own_company(current_user, company_id)
    query = db.query(FinanceEntry).filter(FinanceEntry.company_id == current_user.company_id)
    if product_id:
        query = query.filter(FinanceEntry.product_id == product_id)
    if entry_type:
        query = query.filter(FinanceEntry.entry_type == entry_type)
    return list(query.order_by(FinanceEntry.occurred_on.desc()).all())


@router.patch("/entries/{entry_id}", response_model=FinanceEntryRead)
def patch_entry(
    entry_id: str,
    payload: FinanceEntryUpdate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> FinanceEntry:
    entry = db.get(FinanceEntry, entry_id)
    if entry is None or entry.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Finance entry not found")
    try:
        return update_entry(db, entry_id=entry_id, updates=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/summary", response_model=FinanceSummary)
def get_summary(
    company_id: str,
    product_id: str | None = None,
    since: date | None = None,
    until: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinanceSummary:
    require_own_company(current_user, company_id)
    return summarize_finances(
        db, company_id=company_id, product_id=product_id, since=since, until=until
    )
