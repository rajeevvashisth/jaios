def test_health_reports_database_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"


def test_metrics_endpoint_exposes_prometheus_text_format(client):
    # Exercise a request first so at least one http_requests_total series exists.
    client.get("/health")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "jaios_http_requests_total" in resp.text


def test_requests_get_a_request_id_header(client):
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers


def test_request_id_is_honored_if_client_supplies_one(client):
    resp = client.get("/health", headers={"X-Request-ID": "my-custom-id"})
    assert resp.headers["X-Request-ID"] == "my-custom-id"
