from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_own_company
from app.models.product import Product
from app.models.user import User
from app.schemas.reports import CeoSummary, ProductStatusReport
from app.services.reports_service import get_ceo_summary, get_product_status_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/ceo-summary", response_model=CeoSummary)
def ceo_summary(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CeoSummary:
    require_own_company(current_user, company_id)
    return get_ceo_summary(db, company_id=company_id)


@router.get("/product-status/{product_id}", response_model=ProductStatusReport)
def product_status(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductStatusReport:
    product = db.get(Product, product_id)
    if product is None or product.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        return get_product_status_report(db, product_id=product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
