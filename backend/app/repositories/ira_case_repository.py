from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ira_case import IraCase
from app.models.municipality import Municipality


class IraCaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_filtered(
        self,
        municipality_id: int | None = None,
        year: int | None = None,
        epidemiological_week: int | None = None,
    ) -> list[IraCase]:
        statement = select(IraCase)
        if municipality_id is not None:
            statement = statement.where(IraCase.municipality_id == municipality_id)
        if year is not None:
            statement = statement.where(IraCase.year == year)
        if epidemiological_week is not None:
            statement = statement.where(IraCase.epidemiological_week == epidemiological_week)
        statement = statement.order_by(IraCase.year, IraCase.epidemiological_week, IraCase.municipality_id)
        return list(self.db.scalars(statement).all())

    def get_total_cases(self) -> int:
        statement = select(func.coalesce(func.sum(IraCase.cases), 0))
        return self.db.scalar(statement) or 0

    def count_all(self) -> int:
        return self.db.scalar(select(func.count()).select_from(IraCase)) or 0

    def get_cases_by_municipality(self) -> list[tuple[str, int]]:
        statement = (
            select(Municipality.name, func.sum(IraCase.cases).label("case_total"))
            .join(IraCase, IraCase.municipality_id == Municipality.id)
            .group_by(Municipality.id, Municipality.name)
            .order_by(func.sum(IraCase.cases).desc(), Municipality.name)
        )
        return [(name, total) for name, total in self.db.execute(statement).all()]

    def get_latest_period(self) -> tuple[int, int] | None:
        statement = (
            select(IraCase.year, IraCase.epidemiological_week)
            .order_by(IraCase.year.desc(), IraCase.epidemiological_week.desc())
            .limit(1)
        )
        return self.db.execute(statement).one_or_none()
