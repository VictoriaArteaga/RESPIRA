from pathlib import Path

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ira_case import IraCase
from app.models.municipality import Municipality


SIMULATED_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "simulated" / "ira_cases.csv"
SYNTHETIC_DATA_LABEL = "DATOS SINTÉTICOS DE PRUEBA"


def seed_simulated_data(db: Session) -> None:
    existing_cases = db.scalar(select(func.count()).select_from(IraCase)) or 0
    if existing_cases:
        return

    data = pd.read_csv(SIMULATED_DATA_PATH)
    # La etiqueta explícita evita confundir este conjunto de prueba con registros oficiales.
    required_columns = {
        "municipality",
        "department",
        "latitude",
        "longitude",
        "epidemiological_week",
        "year",
        "cases",
        "temperature",
        "precipitation",
        "humidity",
        "data_source",
    }
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"The synthetic dataset is missing columns: {', '.join(sorted(missing_columns))}")
    if set(data["data_source"].dropna().unique()) != {SYNTHETIC_DATA_LABEL}:
        raise ValueError("The dataset must be clearly labeled as synthetic test data.")

    municipalities: dict[str, Municipality] = {}
    for row in data.itertuples(index=False):
        municipality = municipalities.get(row.municipality)
        if municipality is None:
            municipality = db.scalar(
                select(Municipality).where(Municipality.name == row.municipality)
            )
            if municipality is None:
                municipality = Municipality(
                    name=row.municipality,
                    department=row.department,
                    latitude=row.latitude,
                    longitude=row.longitude,
                )
                db.add(municipality)
                db.flush()
            municipalities[row.municipality] = municipality

        db.add(
            IraCase(
                municipality_id=municipality.id,
                epidemiological_week=row.epidemiological_week,
                year=row.year,
                cases=row.cases,
                temperature=row.temperature,
                precipitation=row.precipitation,
                humidity=row.humidity,
            )
        )
