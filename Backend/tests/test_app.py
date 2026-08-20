"""Smoke tests for the FastAPI application shell."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check_returns_version_and_component_status():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["components"][0]["name"] == "api"
    assert response.headers["X-Request-ID"]


def test_root_describes_api():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "AgentGuard"
    assert response.json()["docs_url"] == "/docs"


def test_openapi_contains_evaluation_routes():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/evaluations/run" in paths
    assert "/api/v1/evaluations/batch" in paths
    assert "/api/v1/evaluations/agents/{agent_id}/history" in paths


def test_security_headers_are_present():
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_oversized_request_is_rejected_before_handler():
    response = client.post(
        "/api/v1/evaluations/compare",
        content="{}",
        headers={"content-length": str(20 * 1024 * 1024)},
    )
    assert response.status_code == 413
