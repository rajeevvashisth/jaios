from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


def register_user(db: Session, *, company_id: str, email: str, password: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ValueError(f"A user with email '{email}' already exists")

    # Classic self-hosted-app bootstrap: the first user registered for a
    # company becomes its admin, everyone after that is a plain member.
    is_first_user_for_company = db.scalar(select(User).where(User.company_id == company_id)) is None
    user = User(
        company_id=company_id,
        email=email,
        hashed_password=hash_password(password),
        role="admin" if is_first_user_for_company else "member",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
