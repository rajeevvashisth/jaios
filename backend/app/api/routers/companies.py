from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)) -> list[Company]:
    return list(db.query(Company).all())


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: str, db: Session = Depends(get_db)) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: str, payload: CompanyUpdate, db: Session = Depends(get_db)
) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
