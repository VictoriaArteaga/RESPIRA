"""Predicciones experimentales de atenciones por IRA (<5 años) a 2 y 3 semanas, por municipio (código DIVIPOLA).

Trabajan sobre data/respira_v2 y los modelos de backend/ml_artifacts; no consultan ni modifican la base de datos.
"""
from fastapi import APIRouter, HTTPException, Query

from app.ml.service import ForecastUnavailable, get_forecast_service

router = APIRouter()


def _service():
    try:
        return get_forecast_service()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=f"Modelos o dataset no disponibles: {error}") from error


@router.get("/status")
def forecast_status() -> dict:
    """Indica si la IA está lista (modelos entrenados y dataset presente)."""
    try:
        service = get_forecast_service()
    except FileNotFoundError as error:
        return {"available": False, "reason": str(error)}
    return {"available": True, "municipalities": len(service.names), "trained_at": service.metrics["generado_utc"]}


@router.get("/models")
def forecast_models() -> dict:
    """Modelos servidos, variables y resultados reales de evaluación (validación 2019, prueba 2022, pandemia aparte)."""
    return _service().models_summary()


@router.get("/municipalities")
def forecast_municipalities() -> dict:
    return {"municipalities": _service().list_municipalities()}


@router.get("/municipalities/{divipola_code}")
def forecast_municipality(divipola_code: str,
                          year: int | None = Query(default=None, ge=2012, le=2022),
                          week: int | None = Query(default=None, ge=1, le=53),
                          model: str | None = Query(default=None, pattern="^(base_global|modelo_a|modelo_b)$")) -> dict:
    """Predicción a t+2 y t+3 desde la última semana con dato, o desde (year, week) para comparar con lo observado."""
    try:
        return _service().forecast(divipola_code, year, week, model)
    except ForecastUnavailable as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
