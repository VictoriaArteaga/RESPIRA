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
