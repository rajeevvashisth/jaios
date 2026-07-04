from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_current_workspace_id,
    get_db,
    require_role,
)
from app.models.company import Company
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead)
def create_company(
    payload: CompanyCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Company:
    # Intentionally reachable without auth — same bootstrap reasoning as
    # /auth/register: there's no user to authenticate as before the very
    # first company (and its workspace) exists. Two paths:
    #   - no workspace_id: bootstrap a brand new workspace for this
    #     company, anonymous or not (this is how the first company in a
    #     fresh install gets created).
    #   - workspace_id given: adding a second company to an *existing*
    #     workspace, which does require being signed in as a member of
    #     that workspace — otherwise anyone could attach a company to a
    #     workspace they merely guessed the id of.
    if payload.workspace_id:
        if current_user is None:
            raise HTTPException(
                status_code=403, detail="Sign in to add a company to an existing workspace"
            )
        if get_current_workspace_id(db, current_user) != payload.workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized for this workspace")
        workspace_id = payload.workspace_id
    else:
        workspace = Workspace(name=f"{payload.name} Workspace")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        workspace_id = workspace.id

    company = Company(**payload.model_dump(exclude={"workspace_id"}), workspace_id=workspace_id)
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
