from finacplus_pipeline import create_app


def test_health_endpoint_reports_ok():
    client = create_app().test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_ready_endpoint_reports_ready():
    client = create_app().test_client()

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_metrics_endpoint_is_prometheus_compatible():
    client = create_app().test_client()

    response = client.get("/metrics")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "text/plain" in response.content_type
    assert "finacplus_app_up 1" in text
    assert "finacplus_app_uptime_seconds" in text


def test_version_endpoint_contains_build_metadata(monkeypatch):
    monkeypatch.setenv("BUILD_SHA", "abc123")
    monkeypatch.setenv("APP_ENV", "test")
    client = create_app().test_client()

    response = client.get("/version")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["build_sha"] == "abc123"
    assert payload["environment"] == "test"
