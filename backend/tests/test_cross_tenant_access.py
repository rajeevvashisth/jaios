"""Guards the auth/company-scoping boundary added across every router.

Before this, only /workflows/{id}/approve required auth at all, and
nothing anywhere verified a company_id in a request actually belonged to
the caller. These tests register two independent companies/users and
confirm each of the representative routers actually enforces both halves
of that boundary: unauthenticated is rejected, and authenticated-but-
wrong-company is rejected too — not just "authenticated is allowed"."""


def _register_and_login(client, name: str) -> tuple[str, dict[str, str]]:
    company = client.post("/api/companies", json={"name": name}).json()
    email = f"{company['id']}@example.com"
    client.post(
        "/api/auth/register",
        json={"company_id": company["id"], "email": email, "password": "pw12345"},
    )
    token = client.post("/api/auth/login", json={"email": email, "password": "pw12345"}).json()[
        "access_token"
    ]
    return company["id"], {"Authorization": f"Bearer {token}"}


def test_companies_list_is_unauthenticated_401(client):
    resp = client.get("/api/companies")
    assert resp.status_code == 401


def test_companies_list_returns_only_own_company(client):
    company_a, headers_a = _register_and_login(client, "Tenant A")
    company_b, _headers_b = _register_and_login(client, "Tenant B")

    resp = client.get("/api/companies", headers=headers_a)
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert ids == [company_a]
    assert company_b not in ids


def test_get_other_companys_company_by_id_is_404(client):
    _company_a, headers_a = _register_and_login(client, "Tenant C")
    company_b, _headers_b = _register_and_login(client, "Tenant D")

    resp = client.get(f"/api/companies/{company_b}", headers=headers_a)
    assert resp.status_code == 404


def test_product_create_rejects_mismatched_company_id(client):
    company_a, headers_a = _register_and_login(client, "Tenant E")
    company_b, _headers_b = _register_and_login(client, "Tenant F")

    resp = client.post(
        "/api/products",
        json={"company_id": company_b, "name": "Cross-tenant product"},
        headers=headers_a,
    )
    assert resp.status_code == 403


def test_product_list_only_returns_own_companys_products(client):
    company_a, headers_a = _register_and_login(client, "Tenant G")
    company_b, headers_b = _register_and_login(client, "Tenant H")

    client.post(
        "/api/products", json={"company_id": company_a, "name": "A Product"}, headers=headers_a
    )
    client.post(
        "/api/products", json={"company_id": company_b, "name": "B Product"}, headers=headers_b
    )

    resp = client.get("/api/products", headers=headers_a)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["A Product"]


def test_get_other_companys_product_by_id_is_404(client):
    company_a, headers_a = _register_and_login(client, "Tenant I")
    _company_b, headers_b = _register_and_login(client, "Tenant J")

    created = client.post(
        "/api/products",
        json={"company_id": company_a, "name": "Private product"},
        headers=headers_a,
    ).json()

    resp = client.get(f"/api/products/{created['id']}", headers=headers_b)
    assert resp.status_code == 404


def test_task_create_and_list_are_company_scoped(client):
    company_a, headers_a = _register_and_login(client, "Tenant K")
    company_b, headers_b = _register_and_login(client, "Tenant L")

    client.post("/api/tasks", json={"company_id": company_a, "title": "A task"}, headers=headers_a)
    client.post("/api/tasks", json={"company_id": company_b, "title": "B task"}, headers=headers_b)

    resp = client.get("/api/tasks", headers=headers_a)
    assert [t["title"] for t in resp.json()] == ["A task"]


def test_finance_list_rejects_mismatched_company_id(client):
    company_a, headers_a = _register_and_login(client, "Tenant M")
    company_b, _headers_b = _register_and_login(client, "Tenant N")

    resp = client.get(f"/api/finance/entries?company_id={company_b}", headers=headers_a)
    assert resp.status_code == 403


def test_finance_entries_are_unauthenticated_401(client):
    resp = client.get("/api/finance/entries?company_id=whatever")
    assert resp.status_code == 401


def test_compliance_obligations_are_company_scoped(client):
    company_a, headers_a = _register_and_login(client, "Tenant O")
    company_b, headers_b = _register_and_login(client, "Tenant P")

    client.post(
        "/api/compliance/obligations",
        json={"company_id": company_a, "title": "A obligation", "category": "tax"},
        headers=headers_a,
    )
    client.post(
        "/api/compliance/obligations",
        json={"company_id": company_b, "title": "B obligation", "category": "tax"},
        headers=headers_b,
    )

    resp = client.get(f"/api/compliance/obligations?company_id={company_a}", headers=headers_a)
    assert [o["title"] for o in resp.json()] == ["A obligation"]


def test_workflow_start_rejects_mismatched_company_id(client):
    company_a, headers_a = _register_and_login(client, "Tenant Q")
    company_b, _headers_b = _register_and_login(client, "Tenant R")

    resp = client.post(
        "/api/workflows/start",
        json={
            "graph_name": "task_delegation",
            "company_id": company_b,
            "input": {"goal": "do something"},
        },
        headers=headers_a,
    )
    assert resp.status_code == 403


def test_get_other_companys_workflow_run_is_404(client, db_session):
    # Insert the run directly rather than going through /workflows/start —
    # this test only exercises the ownership check on GET /workflows/{id},
    # and actually running the multi-agent graph would write real
    # WorkflowStep/audit rows into the shared test database, which other
    # tests (e.g. test_governance.py's exact-count audit log assertions)
    # assume nothing else does.
    from app.models.workflow import WorkflowRun

    company_a, headers_a = _register_and_login(client, "Tenant S")
    _company_b, headers_b = _register_and_login(client, "Tenant T")

    run = WorkflowRun(graph_name="task_delegation", initiating_actor="human", company_id=company_a)
    db_session.add(run)
    db_session.commit()

    resp = client.get(f"/api/workflows/{run.id}", headers=headers_b)
    assert resp.status_code == 404


def test_agents_patch_requires_admin_role(client, db_session):
    from app.core.security import create_access_token
    from app.models.company import Company
    from app.services.user_service import register_user

    company = Company(name="Agents Role Co")
    db_session.add(company)
    db_session.commit()
    user = register_user(
        db_session, company_id=company.id, email="member@example.com", password="pw"
    )
    user.role = "member"
    db_session.commit()
    token = create_access_token(subject=user.id, extra_claims={"role": "member"})

    resp = client.patch(
        "/api/agents/ceo",
        json={"enabled": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_memory_rejects_scope_owned_by_another_company(client):
    company_a, headers_a = _register_and_login(client, "Tenant U")
    company_b, _headers_b = _register_and_login(client, "Tenant V")

    resp = client.post(
        "/api/memory",
        json={"scope_type": "company", "scope_id": company_b, "content": {"note": "x"}},
        headers=headers_a,
    )
    assert resp.status_code == 404


def test_knowledge_search_rejects_mismatched_company_id(client):
    company_a, headers_a = _register_and_login(client, "Tenant W")
    company_b, _headers_b = _register_and_login(client, "Tenant X")

    resp = client.post(
        "/api/knowledge/search",
        json={"company_id": company_b, "query": "anything"},
        headers=headers_a,
    )
    assert resp.status_code == 403
