from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.municipality_repository import MunicipalityRepository
from app.schemas.municipality import MunicipalityRead
from app.services.municipality_service import MunicipalityService

router = APIRouter()


def get_municipality_service(db: Session = Depends(get_db)) -> MunicipalityService:
    return MunicipalityService(MunicipalityRepository(db))


@router.get("", response_model=list[MunicipalityRead])
def list_municipalities(
    service: MunicipalityService = Depends(get_municipality_service),
) -> list[MunicipalityRead]:
    return service.list_municipalities()


@router.get("/{municipality_id}", response_model=MunicipalityRead)
def get_municipality(
    municipality_id: int,
    service: MunicipalityService = Depends(get_municipality_service),
) -> MunicipalityRead:
    municipality = service.get_municipality(municipality_id)
    if municipality is None:
        raise HTTPException(status_code=404, detail="Municipality not found.")
    return municipality
