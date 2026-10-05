from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "simulated" / "ira_cases.csv"
DATA_SOURCE = "DATOS SINTÉTICOS DE PRUEBA"
YEARS = range(2023, 2026)
WEEKS = range(1, 53)

MUNICIPALITIES = [
    ("Pasto", 1.2136, -77.2811, 12, 8.4, 82),
    ("Ipiales", 0.8300, -77.6444, 6, 9.1, 78),
    ("Tumaco", 1.8067, -78.7647, 8, 26.0, 86),
    ("Túquerres", 1.0865, -77.6186, 3, 10.2, 80),
    ("Samaniego", 1.3365, -77.5950, 2, 18.0, 84),
    ("La Unión", 1.6045, -77.1310, 2, 19.2, 79),
    ("Sandoná", 1.2867, -77.4680, 2, 18.5, 83),
    ("Cumbal", 0.9080, -77.7910, 2, 8.1, 81),
    ("Barbacoas", 1.6717, -78.1398, 2, 25.0, 88),
    ("Guaitarilla", 1.1310, -77.5480, 1, 14.0, 82),
]


def generate_rows() -> list[dict[str, object]]:
    # La semilla fija hace que el conjunto de prueba sea reproducible en cada generación.
    random = np.random.default_rng(2025)
    rows: list[dict[str, object]] = []
    for name, latitude, longitude, base_cases, temperature, humidity in MUNICIPALITIES:
        for year in YEARS:
            for week in WEEKS:
                seasonal_peak = 1 + 0.22 * np.sin((week - 10) * 2 * np.pi / 52)
                yearly_change = 1 + 0.03 * (year - min(YEARS))
                cases = max(0, round(base_cases * seasonal_peak * yearly_change + random.normal(0, 1.5)))
                rainfall = max(0, 100 + 55 * np.sin((week + 4) * 2 * np.pi / 52) + random.normal(0, 18))
                rows.append(
                    {
                        "municipality": name,
                        "department": "Nariño",
                        "latitude": latitude,
                        "longitude": longitude,
                        "epidemiological_week": week,
                        "year": year,
                        "cases": cases,
                        "temperature": round(temperature + 1.8 * np.sin(week * 2 * np.pi / 52), 1),
                        "precipitation": round(rainfall, 1),
                        "humidity": round(float(np.clip(humidity + random.normal(0, 4), 40, 100)), 1),
                        "data_source": DATA_SOURCE,
                    }
                )
    return rows


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(generate_rows()).to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(MUNICIPALITIES) * len(YEARS) * len(WEEKS)} synthetic records at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
