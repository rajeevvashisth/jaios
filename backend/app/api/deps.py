from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

__all__ = ["get_db", "get_current_user", "require_role", "require_own_company"]

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return user


def require_role(*roles: str) -> Callable[[User], User]:
    """Dependency factory: ``Depends(require_role("admin", "member"))``
    rejects with 403 unless the authenticated user's role is one of those
    listed. This is a coarse floor for actions humans take (deciding
    approvals, managing users) — separate from and unrelated to agents'
    tool/approval permissions, which come from ``AgentSpec``."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role in {roles}, has '{current_user.role}'",
            )
        return current_user

    return dependency


def require_own_company(current_user: User, company_id: str) -> None:
    """Raise 403 unless ``company_id`` matches the authenticated user's own
    company. Use this for endpoints that take a ``company_id`` directly as a
    known, explicit parameter (list/create). For endpoints that load a
    specific resource by id instead, check the loaded row's ``company_id``
    and raise 404 (not 403) so a guessed id from another tenant doesn't even
    confirm the resource exists."""
    if company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this company"
        )
