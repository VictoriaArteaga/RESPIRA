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
