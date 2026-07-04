import pytest

from app.services.user_service import authenticate_user, register_user


def test_first_user_for_company_becomes_admin(db_session, make_company):
    company = make_company("Auth Co")

    user = register_user(
        db_session, company_id=company.id, email="first@example.com", password="pw"
    )
    assert user.role == "admin"


def test_second_user_for_company_becomes_member(db_session, make_company):
    company = make_company("Auth Co 2")

    register_user(db_session, company_id=company.id, email="first2@example.com", password="pw")
    second = register_user(
        db_session, company_id=company.id, email="second2@example.com", password="pw"
    )
    assert second.role == "member"


def test_duplicate_email_rejected(db_session, make_company):
    company = make_company("Auth Co 3")

    register_user(db_session, company_id=company.id, email="dupe@example.com", password="pw")
    with pytest.raises(ValueError):
        register_user(db_session, company_id=company.id, email="dupe@example.com", password="pw2")


def test_authenticate_user_rejects_wrong_password(db_session, make_company):
    company = make_company("Auth Co 4")
    register_user(db_session, company_id=company.id, email="pw@example.com", password="rightpw")

    assert authenticate_user(db_session, email="pw@example.com", password="wrongpw") is None
    assert authenticate_user(db_session, email="pw@example.com", password="rightpw") is not None


def test_register_login_me_round_trip_over_http(client):
    company_resp = client.post("/api/companies", json={"name": "HTTP Auth Co"})
    assert company_resp.status_code == 200
    company_id = company_resp.json()["id"]

    register_resp = client.post(
        "/api/auth/register",
        json={"company_id": company_id, "email": "http@example.com", "password": "pw12345"},
    )
    assert register_resp.status_code == 200
    assert register_resp.json()["role"] == "admin"

    login_resp = client.post(
        "/api/auth/login", json={"email": "http@example.com", "password": "pw12345"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "http@example.com"


def test_me_without_token_is_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_login_wrong_password_is_401(client):
    company_resp = client.post("/api/companies", json={"name": "Wrong PW Co"})
    company_id = company_resp.json()["id"]
    client.post(
        "/api/auth/register",
        json={"company_id": company_id, "email": "wrongpw@example.com", "password": "rightpw"},
    )

    resp = client.post("/api/auth/login", json={"email": "wrongpw@example.com", "password": "nope"})
    assert resp.status_code == 401
