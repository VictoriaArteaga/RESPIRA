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


def test_risk_map_returns_municipality_comparisons(client: TestClient) -> None:
    response = client.get("/api/risk-map?year=2025&week=40")

    assert response.status_code == 200
    result = response.json()
    assert result["year"] == 2025
    assert result["week"] == 40
    assert len(result["municipalities"]) == 10
    pasto = next(item for item in result["municipalities"] if item["municipality"] == "Pasto")
    assert pasto["current_cases"] is not None
    assert pasto["historical_average"] is not None
    assert pasto["risk_level"] in {"low", "moderate", "high"}


def test_municipality_risk_and_unknown_id(client: TestClient) -> None:
    response = client.get("/api/municipalities/1/risk?year=2025&week=40")
    assert response.status_code == 200
    assert response.json()["risk_level"] in {"low", "moderate", "high"}
    assert client.get("/api/municipalities/99999/risk").status_code == 404


def test_endemic_channel_has_observed_and_historical_percentiles(client: TestClient) -> None:
    response = client.get("/api/municipalities/1/endemic-channel?year=2025")

    assert response.status_code == 200
    result = response.json()
    assert result["year"] == 2025
    assert len(result["weeks"]) == 52
    assert result["weeks"][0]["observed_cases"] >= 0
    assert result["weeks"][0]["lower_limit"] <= result["weeks"][0]["upper_limit"]
    assert result["statistics"]["total_cases"] > 0
    assert client.get("/api/municipalities/99999/endemic-channel").status_code == 404


def test_risk_endpoints_reject_invalid_filters_and_return_empty_for_missing_year(client: TestClient) -> None:
    assert client.get("/api/risk-map?week=54").status_code == 422
    assert client.get("/api/municipalities/1/endemic-channel?year=1900").status_code == 422
    assert client.get("/api/risk-map?year=2099").json()["municipalities"] == []
    assert client.get("/api/municipalities/1/risk?year=2099").json()["risk_level"] == "no_data"


def test_alerts_use_explainable_risk_thresholds_and_filters(client: TestClient) -> None:
    response = client.get("/api/alerts?year=2025&week=40")
    assert response.status_code == 200
    result = response.json()
    assert result["year"] == 2025
    assert result["week"] == 40
    assert all(item["risk_level"] in {"moderate", "high"} for item in result["alerts"])
    assert all(item["observed_cases"] is not None and item["historical_average"] is not None for item in result["alerts"])
    assert all(item["reason"] for item in result["alerts"])
    high_only = client.get("/api/alerts?year=2025&week=40&risk_level=high")
    assert high_only.status_code == 200
    assert all(item["risk_level"] == "high" for item in high_only.json()["alerts"])
    assert client.get("/api/alerts?risk_level=critical").status_code == 422

ALERT_PERIODS = [
    (2023, 1),
    (2023, 2),
    # PERIODS_END
]


@pytest.mark.parametrize(
    "year, week",
    ALERT_PERIODS,
    ids=[f"{year}-week-{week:02d}" for year, week in ALERT_PERIODS],
)
def test_alerts_match_risk_classification_for_each_selected_period(
    client: TestClient, year: int, week: int
) -> None:
    risk_rows = client.get(f"/api/risk-map?year={year}&week={week}").json()["municipalities"]
    alerts = client.get(f"/api/alerts?year={year}&week={week}").json()
    expected = {
        row["municipality_id"]: row
        for row in risk_rows
        if row["risk_level"] in {"moderate", "high"}
    }
    actual = {item["municipality_id"]: item for item in alerts["alerts"]}

    assert alerts["year"] == year
    assert alerts["week"] == week
    assert actual.keys() == expected.keys()
    for municipality_id, alert in actual.items():
        risk = expected[municipality_id]
        assert alert["risk_level"] == risk["risk_level"]
        assert alert["observed_cases"] == risk["current_cases"]
        assert alert["historical_average"] == risk["historical_average"]
        assert alert["variation_percent"] == risk["variation_percent"]
