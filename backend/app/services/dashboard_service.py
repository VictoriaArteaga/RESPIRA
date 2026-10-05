from app.repositories.ira_case_repository import IraCaseRepository
from app.repositories.municipality_repository import MunicipalityRepository
from app.schemas.dashboard import DashboardSummary


class DashboardService:
    def __init__(
        self,
        municipality_repository: MunicipalityRepository,
        case_repository: IraCaseRepository,
    ) -> None:
        self.municipality_repository = municipality_repository
        self.case_repository = case_repository

    def get_summary(self) -> DashboardSummary:
        total_municipalities = self.municipality_repository.count_all()
        total_cases = self.case_repository.get_total_cases()
        total_records = self.case_repository.count_all()
        municipalities_by_cases = self.case_repository.get_cases_by_municipality()
        latest_period = self.case_repository.get_latest_period()

        return DashboardSummary(
            total_municipalities=total_municipalities,
            total_cases=total_cases,
            average_cases=total_cases / total_municipalities if total_municipalities else 0.0,
            municipality_with_most_cases=municipalities_by_cases[0][0] if municipalities_by_cases else None,
            last_epidemiological_week=latest_period[1] if latest_period else None,
            total_records=total_records,
        )
