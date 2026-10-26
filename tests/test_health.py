"""Behavior checks for the scaffold's public HTTP contract."""

from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app


def test_health_contract() -> None:
    """Health remains small, typed, and includes the safety disclaimer header."""
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"] == "application/json"
    disclaimer = response.headers["X-Medical-Disclaimer"]
    assert "ne fournit pas de conseil medical" in disclaimer


def test_openapi_exposes_health_response() -> None:
    """Clients can discover the typed health response through OpenAPI."""
    with TestClient(create_app()) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    operation = schema["paths"]["/health"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
    assert (
        schema["components"]["schemas"]["HealthResponse"]["properties"]["status"][
            "const"
        ]
        == "ok"
    )


def test_unknown_endpoint_is_not_success() -> None:
    """Unimplemented analysis routes must not pretend to work."""
    with TestClient(create_app()) as client:
        response = client.post("/v1/analyze/text", json={"text": "salam"})
    assert response.status_code == 404
