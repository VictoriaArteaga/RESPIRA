from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.municipality import Municipality


class MunicipalityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Municipality]:
        statement = select(Municipality).order_by(Municipality.name)
        return list(self.db.scalars(statement).all())

    def get_by_id(self, municipality_id: int) -> Municipality | None:
        return self.db.get(Municipality, municipality_id)

    def count_all(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Municipality)) or 0
