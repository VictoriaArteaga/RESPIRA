from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.ira_case_repository import IraCaseRepository
from app.schemas.ira_case import IraCaseRead
from app.services.case_service import CaseService

router = APIRouter()


def get_case_service(db: Session = Depends(get_db)) -> CaseService:
    return CaseService(IraCaseRepository(db))


@router.get("", response_model=list[IraCaseRead])
def list_cases(
    municipality_id: int | None = Query(default=None, ge=1),
    year: int | None = Query(default=None, ge=2000),
    epidemiological_week: int | None = Query(default=None, ge=1, le=53),
    service: CaseService = Depends(get_case_service),
) -> list[IraCaseRead]:
    return service.list_cases(municipality_id, year, epidemiological_week)
