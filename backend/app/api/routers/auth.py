from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserRead
from app.services.user_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return register_user(
            db, company_id=payload.company_id, email=payload.email, password=payload.password
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(
        subject=user.id, extra_claims={"role": user.role, "company_id": user.company_id}
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
