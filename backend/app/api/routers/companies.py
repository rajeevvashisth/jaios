from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    # Intentionally unauthenticated: creating a company is the tenant
    # bootstrap step. There is no user to authenticate as until one is
    # registered against a company_id (see POST /auth/register), so this
    # has to stay reachable before any account exists — mirrors why
    # /auth/register and /auth/login are also unauthenticated.
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=list[CompanyRead])
def list_companies(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Company]:
    # Scoped to the caller's own company. This used to return every
    # company in the system with no auth at all — the single biggest
    # cross-tenant leak in the API.
    company = db.get(Company, current_user.company_id)
    return [company] if company else []


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Company:
    company = db.get(Company, company_id)
    if company is None or company.id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: str,
    payload: CompanyUpdate,
    current_user: User = Depends(require_role("admin", "member")),
    db: Session = Depends(get_db),
) -> Company:
    company = db.get(Company, company_id)
    if company is None or company.id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
