from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_municipalities: int
    total_cases: int
    average_cases: float
    municipality_with_most_cases: str | None
    last_epidemiological_week: int | None
    total_records: int
