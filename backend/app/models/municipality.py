from sqlalchemy import CheckConstraint, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Municipality(Base):
    __tablename__ = "municipalities"
    __table_args__ = (
        CheckConstraint("divipola_code IS NULL OR length(divipola_code) = 5", name="ck_municipalities_divipola_len"),
        CheckConstraint("(latitude IS NULL) = (longitude IS NULL)", name="ck_municipalities_coordinates_paired"),
        CheckConstraint("divipola_code ~ '^[0-9]{5}$'", name="ck_municipalities_divipola_format").ddl_if(dialect="postgresql"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    department: Mapped[str] = mapped_column(String(100), default="Nariño")
    # DIVIPOLA identifica al municipio oficial; NULL en los registros sintéticos de la Fase 1.
    divipola_code: Mapped[str | None] = mapped_column(String(5), unique=True)
    # Opcionales: solo se rellenan con coordenadas verificadas, nunca aproximadas ni copiadas de otro municipio.
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    cases: Mapped[list["IraCase"]] = relationship(back_populates="municipality")
