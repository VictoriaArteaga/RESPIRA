from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IraCase(Base):
    __tablename__ = "ira_cases"

    __table_args__ = (
        UniqueConstraint("municipality_id", "year", "epidemiological_week", name="uq_ira_cases_municipality_year_week"),
        CheckConstraint("epidemiological_week BETWEEN 1 AND 53", name="ck_ira_cases_week_range"),
        CheckConstraint("cases >= 0", name="ck_ira_cases_cases_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    municipality_id: Mapped[int] = mapped_column(ForeignKey("municipalities.id"), index=True)
    epidemiological_week: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer, index=True)
    cases: Mapped[int] = mapped_column(Integer)
    temperature: Mapped[float] = mapped_column(Float)
    precipitation: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    municipality: Mapped["Municipality"] = relationship(back_populates="cases")
