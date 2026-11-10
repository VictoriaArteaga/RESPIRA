from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.municipality import Municipality


class MunicipalityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # La API y el mapa actuales exigen coordenadas: los municipios del catálogo oficial sin coordenadas verificadas
    # existen en la base pero no se exponen aquí hasta que el contrato de la API admita ubicaciones ausentes.
    _LOCATED = (Municipality.latitude.is_not(None), Municipality.longitude.is_not(None))

    def list_all(self) -> list[Municipality]:
        statement = select(Municipality).where(*self._LOCATED).order_by(Municipality.name)
        return list(self.db.scalars(statement).all())

    def get_by_id(self, municipality_id: int) -> Municipality | None:
        return self.db.scalar(select(Municipality).where(Municipality.id == municipality_id, *self._LOCATED))

    def count_all(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Municipality).where(*self._LOCATED)) or 0
