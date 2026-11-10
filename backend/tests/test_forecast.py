"""Pruebas de la IA de RESPIRA sobre el dataset real data/respira_v2 y los modelos de backend/ml_artifacts.

Se omiten si el dataset o los modelos entrenados no existen (ver scripts/train_forecast.py)."""
from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.ml.common import ARTIFACT_DIR, DATASET_PATH, classify_trend, epi_week_of
from app.repositories.user_repository import UserRepository

pytestmark = pytest.mark.skipif(not (DATASET_PATH.exists() and (ARTIFACT_DIR / "metrics.json").exists()),
                                reason="Falta el dataset real o los modelos entrenados")

PASTO, ALBAN = "52001", "52019"   # Pasto tiene los tres modelos; Albán solo el base (sin cobertura climática)


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        creds = {"email": "forecast@example.com", "password": "Forecast-2025-ok"}
        c.post("/api/auth/register", json=creds)
        with SessionLocal.begin() as db:
            UserRepository(db).get_by_email(creds["email"]).is_active = True
        c.headers["Authorization"] = "Bearer " + c.post("/api/auth/login", json=creds).json()["access_token"]
        yield c


def test_forecast_requires_authentication() -> None:
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/forecast/models").status_code in (401, 403)


def test_epi_week_rule_matches_verified_anchors() -> None:
    assert epi_week_of(date(2016, 12, 31)) == (2016, 52)
    assert epi_week_of(date(2022, 12, 31)) == (2022, 52)
    assert epi_week_of(date(2023, 1, 14)) == (2023, 2)
    assert epi_week_of(date(2020, 12, 31)) == (2020, 53)


def test_trend_classification() -> None:
    assert classify_trend(130, 100) == "aumento"
    assert classify_trend(70, 100) == "disminucion"
    assert classify_trend(105, 100) == "estable"
    assert classify_trend(2.5, 1) == "estable"        # cambio absoluto menor a 2: ruido
    assert classify_trend(3, 1) == "aumento"          # cambio de 2 atenciones o más y ≥20%
    assert classify_trend(5, None) == "sin_referencia"


def test_status_and_models(client: TestClient) -> None:
    assert client.get("/api/forecast/status").json()["available"] is True
    body = client.get("/api/forecast/models").json()
    assert {m["id"] for m in body["models"]} == {"base_global", "modelo_a", "modelo_b"}
    assert body["models"][0]["horizons"]["2"]["test_2022"]["n"] > 0
    assert "No es un diagnóstico" in body["disclaimer"] or "no es un diagnóstico" in body["disclaimer"].lower()


def test_models_endpoint_reports_attached_public_data_without_using_it_for_training(client: TestClient) -> None:
    ext = client.get("/api/forecast/models").json().get("data_extension")
    if ext is None:
        pytest.skip("Extensión 2023-2025 no generada")
    assert ext["used_for_training"] is False and ext["ira_public_2023_2025"] is False
    assert ext["ira_last_week"] == {"year": 2022, "week": 52} and ext["population_through_year"] == 2025
    assert ext["calendar_weeks"]["2025"] == 53
