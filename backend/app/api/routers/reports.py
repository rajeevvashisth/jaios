from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reports import CeoSummary, ProductStatusReport
from app.services.reports_service import get_ceo_summary, get_product_status_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/ceo-summary", response_model=CeoSummary)
def ceo_summary(company_id: str, db: Session = Depends(get_db)) -> CeoSummary:
    return get_ceo_summary(db, company_id=company_id)


@router.get("/product-status/{product_id}", response_model=ProductStatusReport)
def product_status(product_id: str, db: Session = Depends(get_db)) -> ProductStatusReport:
    try:
        return get_product_status_report(db, product_id=product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
