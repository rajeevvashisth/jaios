import pytest
from fastapi import HTTPException

from app.api.deps import require_role
from app.models.user import User


def _user(role: str) -> User:
    return User(id="u1", company_id="c1", email="u@example.com", hashed_password="x", role=role)


def test_require_role_allows_listed_role():
    dependency = require_role("admin", "member")
    assert dependency(current_user=_user("admin")) is not None
    assert dependency(current_user=_user("member")) is not None


def test_require_role_rejects_unlisted_role():
    dependency = require_role("admin", "member")
    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=_user("viewer"))
    assert exc_info.value.status_code == 403


def test_approve_endpoint_requires_auth(client):
    resp = client.post("/api/workflows/does-not-exist/approve", json={"approve": True})
    assert resp.status_code == 401


def test_approve_endpoint_rejects_viewer_role(client, db_session, make_company):
    from app.core.security import create_access_token
    from app.services.user_service import register_user

    company = make_company("Viewer Approve Co")

    user = register_user(
        db_session, company_id=company.id, email="viewer@example.com", password="pw"
    )
    user.role = "viewer"
    db_session.commit()

    token = create_access_token(subject=user.id, extra_claims={"role": "viewer"})
    resp = client.post(
        "/api/workflows/does-not-exist/approve",
        json={"approve": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
