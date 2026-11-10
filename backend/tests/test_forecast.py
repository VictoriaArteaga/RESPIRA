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


def test_municipalities_cover_all_64_with_model_availability(client: TestClient) -> None:
    items = client.get("/api/forecast/municipalities").json()["municipalities"]
    assert len(items) == 64
    by_code = {m["divipola_code"]: m for m in items}
    assert by_code[PASTO]["available_models"] == ["base_global", "modelo_a", "modelo_b"]
    assert by_code[ALBAN]["available_models"] == ["base_global"]


def test_forecast_default_returns_both_horizons_from_latest_week(client: TestClient) -> None:
    body = client.get(f"/api/forecast/municipalities/{PASTO}").json()
    assert body["model"]["id"] == "base_global" and body["model"]["is_default"] is True
    assert body["origin"]["year"] == 2022 and body["origin"]["week"] == 52 and body["origin"]["is_latest_available"] is True
    h2, h3 = body["predictions"]
    assert (h2["horizon_weeks"], h2["target_year"], h2["target_week"]) == (2, 2023, 2)
    assert (h3["horizon_weeks"], h3["target_year"], h3["target_week"]) == (3, 2023, 3)
    for p in body["predictions"]:
        assert p["interval_low"] <= p["predicted_cases"] <= p["interval_high"] and p["predicted_cases"] >= 0
        assert p["trend"] in {"aumento", "estable", "disminucion"}
        assert p["observed_cases"] is None          # el futuro no se conoce
    assert len(body["history"]) == 104 and body["disclaimer"]
    assert {m["model"] for m in body["comparison"]} == {"modelo_a", "modelo_b"}


def test_increase_signal_is_returned_for_both_horizons_with_honest_context(client: TestClient) -> None:
    body = client.get(f"/api/forecast/municipalities/{PASTO}").json()
    signals = body["increase_signal"]
    assert [s["horizon_weeks"] for s in signals] == [2, 3]
    for s in signals:
        assert 0 <= s["probability"] <= 1 and s["level"] in {"baja", "media", "alta"}
        assert 0 < s["base_increase_rate"] < 1 and s["observed_increase"] is None
    ev = body["signal_evaluation"]["2"]["test_2022"]
    assert ev["auc"] > 0.5 and ev["rate_by_level"]["baja"] < ev["rate_by_level"]["media"] < ev["rate_by_level"]["alta"]
    assert client.get("/api/forecast/models").json()["increase_signal"]["horizons"]["3"]["test_2022"]["n"] > 0


def test_channel_outlook_gives_zone_probabilities_and_beats_chance(client: TestClient) -> None:
    body = client.get(f"/api/forecast/municipalities/{PASTO}").json()
    out = body["channel_outlook"]
    assert [o["horizon_weeks"] for o in out] == [2, 3] and all(o["available"] for o in out)
    for o in out:
        c = o["channel"]
        assert c["p25"] <= c["p50"] <= c["p75"] <= c["p90"]
        assert o["predicted_zone"] in {"dentro", "sobre", "alerta"} and o["observed_zone"] is None
        for kind in ("exceed_p75", "exceed_p90"):
            assert 0 <= o[kind]["probability"] <= 1 and o[kind]["level"] in {"baja", "media", "alta"}
    ev = body["channel_evaluation"]["2"]["p75"]["test_2022"]
    assert ev["auc"] > 0.8 and ev["auc"] > ev["auc_simple_rule"] - 0.001   # honesto: la regla simple ya es fuerte
    assert ev["rate_by_level"]["baja"] < ev["rate_by_level"]["alta"]


def test_channel_unavailable_when_week_has_too_few_reference_years(client: TestClient) -> None:
    # origen 2013 SE10: solo 2012 es año anterior, hay menos de 3 años de referencia y no se inventa un canal
    body = client.get(f"/api/forecast/municipalities/{PASTO}?year=2013&week=10").json()
    assert all(o["available"] is False and "reason" in o for o in body["channel_outlook"])


def test_backtest_signal_reports_what_happened(client: TestClient) -> None:
    body = client.get(f"/api/forecast/municipalities/{PASTO}?year=2022&week=30").json()
    assert all(isinstance(s["observed_increase"], bool) for s in body["increase_signal"])


def test_backtest_includes_observed_value_and_no_leakage(client: TestClient) -> None:
    body = client.get(f"/api/forecast/municipalities/{PASTO}?year=2022&week=30").json()
    assert body["origin"]["is_backtest"] is True
    p2 = body["predictions"][0]
    assert (p2["target_year"], p2["target_week"]) == (2022, 32)
    assert p2["observed_cases"] is not None and p2["absolute_error"] is not None
    # el historial devuelto termina en la semana de referencia: no contiene semanas posteriores
    assert (body["history"][-1]["year"], body["history"][-1]["week"]) == (2022, 30)


def test_municipality_without_climate_coverage_rejects_climate_model_but_serves_base(client: TestClient) -> None:
    ok = client.get(f"/api/forecast/municipalities/{ALBAN}")
    assert ok.status_code == 200 and ok.json()["model"]["id"] == "base_global"
    assert all(v["available_for_municipality"] is False for v in ok.json()["variables"] if v["key"] != "ira_history")
    refused = client.get(f"/api/forecast/municipalities/{ALBAN}?model=modelo_a")
    assert refused.status_code == 422 and "cobertura climática" in refused.json()["detail"]
