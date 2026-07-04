"""HTTP-level checks that the new Workspace/AI-provider endpoints enforce
the same auth + ownership boundary as everything else (see
test_cross_tenant_access.py for the original sweep across the rest of
the API)."""


def _register_and_login(client, name: str) -> tuple[str, str, dict[str, str]]:
    company = client.post("/api/companies", json={"name": name}).json()
    email = f"{company['id']}@example.com"
    client.post(
        "/api/auth/register",
        json={"company_id": company["id"], "email": email, "password": "pw12345"},
    )
    token = client.post("/api/auth/login", json={"email": email, "password": "pw12345"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    workspace_id = client.get("/api/workspaces/me", headers=headers).json()["id"]
    return company["id"], workspace_id, headers


def test_workspace_created_alongside_bootstrap_company(client):
    _company_id, workspace_id, _headers = _register_and_login(client, "Bootstrap Workspace Co")
    assert workspace_id


def test_second_company_in_same_workspace_is_allowed(client):
    _company_id, workspace_id, headers = _register_and_login(client, "Multi Company Co")

    resp = client.post(
        "/api/companies",
        json={"name": "Second Business Unit", "workspace_id": workspace_id},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["workspace_id"] == workspace_id


def test_adding_company_to_someone_elses_workspace_is_rejected(client):
    _a_id, _a_ws, headers_a = _register_and_login(client, "Workspace Owner Co")
    _b_id, workspace_b, _headers_b = _register_and_login(client, "Other Workspace Co")

    resp = client.post(
        "/api/companies",
        json={"name": "Sneaky company", "workspace_id": workspace_b},
        headers=headers_a,
    )
    assert resp.status_code == 403


def test_ai_providers_require_own_workspace(client):
    _a_id, workspace_a, headers_a = _register_and_login(client, "AI Settings Co A")
    _b_id, workspace_b, headers_b = _register_and_login(client, "AI Settings Co B")

    created = client.post(
        "/api/ai/providers",
        json={"workspace_id": workspace_a, "provider": "ollama", "base_url": "http://x:11434"},
        headers=headers_a,
    )
    assert created.status_code == 200

    cross_tenant_create = client.post(
        "/api/ai/providers",
        json={"workspace_id": workspace_a, "provider": "ollama"},
        headers=headers_b,
    )
    assert cross_tenant_create.status_code == 403

    cross_tenant_list = client.get(
        f"/api/ai/providers?workspace_id={workspace_a}", headers=headers_b
    )
    assert cross_tenant_list.status_code == 403

    own_list = client.get(f"/api/ai/providers?workspace_id={workspace_a}", headers=headers_a)
    assert own_list.status_code == 200
    assert len(own_list.json()) == 1


def test_ai_provider_config_never_exposes_raw_api_key(client):
    _a_id, workspace_a, headers_a = _register_and_login(client, "No Leak Co")

    created = client.post(
        "/api/ai/providers",
        json={"workspace_id": workspace_a, "provider": "anthropic", "api_key": "sk-do-not-leak"},
        headers=headers_a,
    ).json()

    assert created["has_api_key"] is True
    assert "api_key" not in created
    assert "sk-do-not-leak" not in str(created)
