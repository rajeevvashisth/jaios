from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_own_company",
    "require_own_workspace",
    "get_current_workspace_id",
]

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


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like ``get_current_user`` but returns ``None`` instead of raising —
    for the few endpoints (company bootstrap) that behave differently for
    a signed-in vs. anonymous caller rather than requiring auth outright."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    user = db.get(User, payload.get("sub"))
    return user if user is not None and user.is_active else None


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


def get_current_workspace_id(db: Session, current_user: User) -> str | None:
    """Resolve the authenticated user's own workspace via their company —
    there's no direct User -> Workspace link (see models/workspace.py's
    docstring on why), so this is the one place that indirection lives."""
    company = db.get(Company, current_user.company_id)
    return company.workspace_id if company else None


def require_own_workspace(db: Session, current_user: User, workspace_id: str) -> None:
    """Raise 403 unless ``workspace_id`` matches the authenticated user's
    own workspace (resolved through their company) — the workspace-level
    equivalent of ``require_own_company``, for AI provider config, usage,
    and policy endpoints that are scoped to the workspace, not a company."""
    if workspace_id != get_current_workspace_id(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this workspace"
        )
