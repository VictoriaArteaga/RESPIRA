from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.ira_case_repository import IraCaseRepository
from app.repositories.municipality_repository import MunicipalityRepository
from app.services.risk_service import RiskService

router = APIRouter()


def get_risk_service(db: Session = Depends(get_db)) -> RiskService:
    return RiskService(MunicipalityRepository(db), IraCaseRepository(db))


@router.get("/alerts")
def get_alerts(year: int | None = Query(default=None, ge=2000), week: int | None = Query(default=None, ge=1, le=53),
               risk_level: str | None = Query(default=None, pattern="^(moderate|high)$"),
               service: RiskService = Depends(get_risk_service)) -> dict:
    """List statistical deviations using the same thresholds as the risk map."""
    return service.alerts(year, week, risk_level)


@router.get("/risk-map")
def get_risk_map(year: int | None = Query(default=None, ge=2000), week: int | None = Query(default=None, ge=1, le=53),
                 service: RiskService = Depends(get_risk_service)) -> dict:
    return service.risk_map(year, week)


@router.get("/municipalities/{municipality_id}/risk")
def get_municipality_risk(municipality_id: int, year: int | None = Query(default=None, ge=2000),
                          week: int | None = Query(default=None, ge=1, le=53),
                          service: RiskService = Depends(get_risk_service)) -> dict:
    result = service.municipality_risk(municipality_id, year, week)
    if result is None:
        raise HTTPException(status_code=404, detail="Municipality not found.")
    return result


@router.get("/municipalities/{municipality_id}/endemic-channel")
def get_endemic_channel(municipality_id: int, year: int | None = Query(default=None, ge=2000),
                        service: RiskService = Depends(get_risk_service)) -> dict:
    result = service.endemic_channel(municipality_id, year)
    if result is None:
        raise HTTPException(status_code=404, detail="Municipality not found.")
    return result
