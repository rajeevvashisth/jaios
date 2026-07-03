from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.compliance import ComplianceObligation
from app.schemas.compliance import ComplianceObligationCreate, ComplianceObligationRead
from app.services.compliance_service import list_obligations, mark_completed, to_read

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


@router.post("/obligations/{obligation_id}/complete", response_model=ComplianceObligationRead)
def complete_obligation(
    obligation_id: str, db: Session = Depends(get_db)
) -> ComplianceObligationRead:
    try:
        return mark_completed(db, obligation_id=obligation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
