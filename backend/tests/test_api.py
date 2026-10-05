from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_returns_service_status(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "RESPIRA API"}


def test_list_municipalities_returns_synthetic_municipalities(client: TestClient) -> None:
    response = client.get("/api/municipalities")

    assert response.status_code == 200
    assert len(response.json()) == 10
    assert response.json()[0]["name"] == "Barbacoas"


def test_get_municipality_returns_details(client: TestClient) -> None:
    municipalities = client.get("/api/municipalities").json()
    municipality_id = next(item["id"] for item in municipalities if item["name"] == "Pasto")

    response = client.get(f"/api/municipalities/{municipality_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Pasto"
    assert response.json()["department"] == "Nariño"


def test_get_unknown_municipality_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/municipalities/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Municipality not found."


def test_list_cases_supports_filters(client: TestClient) -> None:
    response = client.get("/api/cases?municipality_id=1&year=2025&epidemiological_week=40")

    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 1
    assert cases[0]["municipality_id"] == 1
    assert cases[0]["year"] == 2025
    assert cases[0]["epidemiological_week"] == 40


def test_list_cases_rejects_invalid_week(client: TestClient) -> None:
    response = client.get("/api/cases?epidemiological_week=54")

    assert response.status_code == 422


def test_dashboard_is_calculated_from_database(client: TestClient) -> None:
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_municipalities"] == 10
    assert summary["total_records"] == 10 * 3 * 52
    assert summary["total_cases"] > 0
    assert summary["average_cases"] == pytest.approx(summary["total_cases"] / 10)
    assert summary["municipality_with_most_cases"] is not None
    assert summary["last_epidemiological_week"] == 52
