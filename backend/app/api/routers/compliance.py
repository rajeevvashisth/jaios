from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.compliance import ComplianceObligation
from app.schemas.compliance import (
    ComplianceObligationCreate,
    ComplianceObligationRead,
    ComplianceObligationUpdate,
)
from app.services.compliance_framework import seed_india_llp_compliance_framework
from app.services.compliance_service import (
    list_obligations,
    mark_completed,
    to_read,
    update_obligation,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/obligations", response_model=ComplianceObligationRead)
def create_obligation(
    payload: ComplianceObligationCreate, db: Session = Depends(get_db)
) -> ComplianceObligationRead:
    obligation = ComplianceObligation(**payload.model_dump())
    db.add(obligation)
    db.commit()
    db.refresh(obligation)
    return to_read(obligation)


@router.get("/obligations", response_model=list[ComplianceObligationRead])
def get_obligations(
    company_id: str,
    product_id: str | None = None,
    include_completed: bool = False,
    db: Session = Depends(get_db),
) -> list[ComplianceObligationRead]:
    return list_obligations(
        db, company_id=company_id, product_id=product_id, include_completed=include_completed
    )


@router.patch("/obligations/{obligation_id}", response_model=ComplianceObligationRead)
def patch_obligation(
    obligation_id: str, payload: ComplianceObligationUpdate, db: Session = Depends(get_db)
) -> ComplianceObligationRead:
    try:
        return update_obligation(db, obligation_id=obligation_id, updates=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/obligations/{obligation_id}/complete", response_model=ComplianceObligationRead)
def complete_obligation(
    obligation_id: str, db: Session = Depends(get_db)
) -> ComplianceObligationRead:
    try:
        return mark_completed(db, obligation_id=obligation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/seed-india-llp-framework", response_model=list[ComplianceObligationRead])
def seed_india_llp_framework(
    company_id: str, db: Session = Depends(get_db)
) -> list[ComplianceObligationRead]:
    """Seed the standard India-LLP compliance checklist for a company. Not
    company-specific — reusable for any Indian LLP onboarded onto JAIOS.
    Safe-ish to call more than once, but will create duplicate rows if you
    do; intended as a one-time bootstrap per company."""
    obligations = seed_india_llp_compliance_framework(db, company_id=company_id)
    return [to_read(o) for o in obligations]
