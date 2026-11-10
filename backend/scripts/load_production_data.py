"""Carga en municipalities / ira_cases los datos que muestra la aplicación web (2012-2025, 64 municipios).

Reglas (decididas con la autora del proyecto):
  * 2012-2022: casos REALES de IRA (SIVIGILA 995, último reporte) de data/respira_v2/dataset_entrenamiento.csv.
    Las semanas sin dato en la fuente se omiten; no se inventan ceros.
  * 2023-2025: casos SIMULADOS (backend/data/simulated/ira_cases.csv, 10 municipios); no hay datos públicos reales.
  * Clima (temperatura, precipitación, humedad): se usa el valor REAL cuando existe; si falta, se rellena con un valor
    SIMULADO reproducible (semilla fija). La tabla no guarda el origen de cada valor.
  * Coordenadas: las oficiales de cabecera municipal (dataset_geografico.csv).

Uso (desde backend, con .env): python scripts/load_production_data.py            -> solo resumen (no escribe)
                              python scripts/load_production_data.py --apply    -> escribe en la base
"""
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

V2 = ROOT / "data" / "respira_v2"
SIM = ROOT / "backend" / "data" / "simulated" / "ira_cases.csv"
# (temperatura base °C, humedad base %) de los 10 municipios del generador sintético; sirven si no hay clima real.
SIM_BASE = {"Pasto": (8.4, 82), "Ipiales": (9.1, 78), "Tumaco": (26.0, 86), "Túquerres": (10.2, 80), "Samaniego": (18.0, 84),
            "La Unión": (19.2, 79), "Sandoná": (18.5, 83), "Cumbal": (8.1, 81), "Barbacoas": (25.0, 88), "Guaitarilla": (14.0, 82)}
SMALL = {"de", "del", "la", "las", "los", "y"}


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(text).lower()) if unicodedata.category(c) != "Mn").strip()


def pretty(name: str) -> str:
    words = name.lower().split()
    return " ".join(w if (i and w in SMALL) else w.capitalize() for i, w in enumerate(words))


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(2025)
    geo = pd.read_csv(V2 / "dataset_geografico.csv", dtype={"codigo_divipola": str}, encoding="utf-8-sig")
    munis = pd.DataFrame({"divipola_code": geo.codigo_divipola, "name": geo.municipio.map(pretty), "department": "Nariño",
                          "latitude": geo.latitud_cabecera, "longitude": geo.longitud_cabecera})
    code_by_name = {norm(n): c for n, c in zip(munis.name, munis.divipola_code)}
    code_by_name["tumaco"] = code_by_name.get("san andres de tumaco", code_by_name.get("tumaco"))

    real = pd.read_csv(V2 / "dataset_entrenamiento.csv", dtype={"codigo_divipola": str}, encoding="utf-8-sig")
    real = real[real.ira_0_4.notna()]
    r = pd.DataFrame({"divipola_code": real.codigo_divipola, "year": real.anio, "epidemiological_week": real.semana_epidemiologica,
                      "cases": real.ira_0_4.round().astype(int), "temperature": real.temp_media,
                      "precipitation": real.precipitacion, "humidity": real.humedad_relativa})

    sim = pd.read_csv(SIM)
    sim["divipola_code"] = sim.municipality.map(lambda n: code_by_name.get(norm(n)))
    if sim.divipola_code.isna().any():
        raise SystemExit(f"Municipios simulados sin código DIVIPOLA: {sorted(sim[sim.divipola_code.isna()].municipality.unique())}")
    s = sim.rename(columns={"year": "year"})[["divipola_code", "year", "epidemiological_week", "cases", "temperature",
                                              "precipitation", "humidity"]].copy()
    # Clima público real 2023-2025 (pocas estaciones): reemplaza al simulado donde existe.
    ctx = pd.read_csv(V2 / "dataset_contexto_2023_2025.csv", dtype={"codigo_divipola": str}, encoding="utf-8-sig")
    ctx = ctx.rename(columns={"codigo_divipola": "divipola_code", "anio": "year", "temp_media": "t", "humedad_relativa": "h",
                              "precipitacion": "p"})[["divipola_code", "year", "semana_epidemiologica", "t", "h", "p"]]
    s = s.merge(ctx.rename(columns={"semana_epidemiologica": "epidemiological_week"}), how="left",
                on=["divipola_code", "year", "epidemiological_week"])
    for col, real_col in (("temperature", "t"), ("humidity", "h"), ("precipitation", "p")):
        s[col] = s[real_col].where(s[real_col].notna(), s[col])
    s = s.drop(columns=["t", "h", "p"])

    cases = pd.concat([r, s], ignore_index=True)
    stats = {}
    for col in ("temperature", "precipitation", "humidity"):
        stats[col] = (cases[col].mean(), cases.groupby("divipola_code")[col].mean())
    n_real_missing = {c: int(cases[c].isna().sum()) for c in stats}
    name_by_code = dict(zip(munis.divipola_code, munis.name))
    for col, (dept_mean, by_muni) in stats.items():
        miss = cases[col].isna()
        if not miss.any():
            continue
        base = cases.loc[miss, "divipola_code"].map(by_muni)
        if col != "precipitation":
            idx = 0 if col == "temperature" else 1
            fallback = cases.loc[miss, "divipola_code"].map(lambda c: SIM_BASE.get(name_by_code[c], (None, None))[idx])
            base = base.fillna(fallback)
        base = base.fillna(dept_mean)
        week = cases.loc[miss, "epidemiological_week"]
        if col == "temperature":
            val = base + 1.8 * np.sin(week * 2 * np.pi / 52) + rng.normal(0, 0.4, miss.sum())
        elif col == "precipitation":
            val = np.maximum(0, base * (1 + 0.4 * np.sin((week + 4) * 2 * np.pi / 52)) + rng.normal(0, 0.25 * base))
        else:
            val = np.clip(base + rng.normal(0, 4, miss.sum()), 40, 100)
        cases.loc[miss, col] = val.round(1)
    cases.attrs["relleno_simulado"] = n_real_missing
    return munis, cases


def main() -> None:
    munis, cases = build()
    print(f"Municipios: {len(munis)} | filas de casos: {len(cases)} | años {cases.year.min()}-{cases.year.max()}")
    print("Valores de clima rellenados con simulación:", cases.attrs["relleno_simulado"])
    print(cases.groupby("year").agg(municipios=("divipola_code", "nunique"), filas=("cases", "size")).T.to_string())
    dup = cases.duplicated(["divipola_code", "year", "epidemiological_week"]).sum()
    if dup or cases[["temperature", "precipitation", "humidity"]].isna().any().any():
        raise SystemExit(f"Datos inválidos (duplicados={dup} o clima vacío).")
    if "--apply" not in sys.argv:
        print("\nSimulacro: no se escribió nada. Use --apply para cargar.")
        return

    from sqlalchemy import insert, select, func
    from app.core.database import SessionLocal
    from app.models.ira_case import IraCase
    from app.models.municipality import Municipality

    with SessionLocal.begin() as db:
        if db.scalar(select(func.count()).select_from(Municipality)) or db.scalar(select(func.count()).select_from(IraCase)):
            raise SystemExit("Las tablas no están vacías; se cancela para no duplicar ni sobrescribir datos.")
        db.execute(insert(Municipality), munis.astype(object).where(munis.notna(), None).to_dict("records"))
        ids = dict(db.execute(select(Municipality.divipola_code, Municipality.id)).all())
        cases["municipality_id"] = cases.divipola_code.map(ids)
        rows = cases.drop(columns="divipola_code").to_dict("records")
        for i in range(0, len(rows), 5000):
            db.execute(insert(IraCase), rows[i:i + 5000])
    print("Carga completada.")


if __name__ == "__main__":
    main()
