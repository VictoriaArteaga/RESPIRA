from app.models.ira_case import IraCase
from app.repositories.ira_case_repository import IraCaseRepository


class CaseService:
    def __init__(self, repository: IraCaseRepository) -> None:
        self.repository = repository

    def list_cases(
        self,
        municipality_id: int | None = None,
        year: int | None = None,
        epidemiological_week: int | None = None,
    ) -> list[IraCase]:
        return self.repository.list_filtered(municipality_id, year, epidemiological_week)
