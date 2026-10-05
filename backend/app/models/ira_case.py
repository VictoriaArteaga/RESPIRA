from sqlalchemy import ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IraCase(Base):
    __tablename__ = "ira_cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    municipality_id: Mapped[int] = mapped_column(ForeignKey("municipalities.id"), index=True)
    epidemiological_week: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer, index=True)
    cases: Mapped[int] = mapped_column(Integer)
    temperature: Mapped[float] = mapped_column(Float)
    precipitation: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    municipality: Mapped["Municipality"] = relationship(back_populates="cases")
