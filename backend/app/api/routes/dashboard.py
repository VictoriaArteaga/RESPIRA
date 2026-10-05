from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.ira_case_repository import IraCaseRepository
from app.repositories.municipality_repository import MunicipalityRepository
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(MunicipalityRepository(db), IraCaseRepository(db))


@router.get("", response_model=DashboardSummary)
def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    return service.get_summary()
