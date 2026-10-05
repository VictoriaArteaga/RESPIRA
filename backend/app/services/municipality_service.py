from app.models.municipality import Municipality
from app.repositories.municipality_repository import MunicipalityRepository


class MunicipalityService:
    def __init__(self, repository: MunicipalityRepository) -> None:
        self.repository = repository

    def list_municipalities(self) -> list[Municipality]:
        return self.repository.list_all()

    def get_municipality(self, municipality_id: int) -> Municipality | None:
        return self.repository.get_by_id(municipality_id)
