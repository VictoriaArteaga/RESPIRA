import threading

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ira_case import IraCase
from app.models.municipality import Municipality


# Copia en memoria de las columnas que usa el cálculo de riesgo. Se valida con una consulta mínima (cantidad y último id)
# en cada uso, de modo que una recarga de datos invalida la copia sin esperar a que caduque.
_RISK_CACHE: dict = {"key": None, "rows": []}
_RISK_LOCK = threading.Lock()


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

    def risk_rows(self) -> list:
        """Casos mínimos (municipio, año, semana, casos) para el riesgo y el canal endémico, con caché validada."""
        fingerprint = self.db.execute(select(func.count(IraCase.id), func.max(IraCase.id), func.sum(IraCase.cases))).one()
        key = tuple(fingerprint)
        with _RISK_LOCK:
            if _RISK_CACHE["key"] == key:
                return _RISK_CACHE["rows"]
        statement = select(IraCase.municipality_id, IraCase.year, IraCase.epidemiological_week, IraCase.cases).order_by(
            IraCase.year, IraCase.epidemiological_week, IraCase.municipality_id
        )
        rows = list(self.db.execute(statement).all())
        with _RISK_LOCK:
            _RISK_CACHE["key"], _RISK_CACHE["rows"] = key, rows
        return rows

    def summary_by_municipality(self) -> list[tuple[int, int, int, int]]:
        """(municipio, casos totales, último año, última semana) en una sola consulta agregada."""
        statement = select(
            IraCase.municipality_id,
            func.sum(IraCase.cases),
            func.max(IraCase.year * 100 + IraCase.epidemiological_week),
        ).group_by(IraCase.municipality_id)
        return [(mid, int(total), int(period) // 100, int(period) % 100) for mid, total, period in self.db.execute(statement).all()]
