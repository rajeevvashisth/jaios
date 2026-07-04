from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_own_company, require_role
from app.models.compliance import ComplianceObligation
from app.models.user import User
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
    payload: ComplianceObligationCreate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> ComplianceObligationRead:
    require_own_company(current_user, payload.company_id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ComplianceObligationRead]:
    require_own_company(current_user, company_id)
    return list_obligations(
        db, company_id=company_id, product_id=product_id, include_completed=include_completed
    )


@router.patch("/obligations/{obligation_id}", response_model=ComplianceObligationRead)
def patch_obligation(
    obligation_id: str,
    payload: ComplianceObligationUpdate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> ComplianceObligationRead:
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None or obligation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Compliance obligation not found")
    try:
        return update_obligation(db, obligation_id=obligation_id, updates=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/obligations/{obligation_id}/complete", response_model=ComplianceObligationRead)
def complete_obligation(
    obligation_id: str,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> ComplianceObligationRead:
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None or obligation.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Compliance obligation not found")
    try:
        return mark_completed(db, obligation_id=obligation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/seed-india-llp-framework", response_model=list[ComplianceObligationRead])
def seed_india_llp_framework(
    company_id: str,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> list[ComplianceObligationRead]:
    """Seed the standard India-LLP compliance checklist for a company. Not
    company-specific — reusable for any Indian LLP onboarded onto JAIOS.
    Safe-ish to call more than once, but will create duplicate rows if you
    do; intended as a one-time bootstrap per company."""
    require_own_company(current_user, company_id)
    obligations = seed_india_llp_compliance_framework(db, company_id=company_id)
    return [to_read(o) for o in obligations]
