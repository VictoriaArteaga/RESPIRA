"""Procesamiento climático IDEAM: estaciones, series diarias, calendario verificado y agregación semanal.

Reglas aprobadas (ver config.py): temperatura >=6/7 días válidos por variable; precipitación 7/7 (y solo si la
semántica está confirmada); sin imputación ni interpolación; solo estación del mismo municipio; Aldana excluida
(SERIE_NO_CONFIABLE); Chachagüí sin estación validada; semanas solo para años con calendario verificado.
"""
from __future__ import annotations
import re, unicodedata
from datetime import date, timedelta
import pandas as pd
from . import config as C

TEMP_FOLDER = "TemperaturaNacionalDiaria"
PREC_FOLDER = "PrecipitacionNacionalDiaria"
# Reglas de mapeo manual documentadas en la quinta auditoría (an8.py): nombre del catálogo IDEAM -> nombre DANE.
MANUAL_NAME_MAP = {"TUMACO": "52835", "EL TABLON": "52258", "SANTA CRUZ": "52699"}


def nz(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^A-Z ]", "", s).strip()


def read_csv_any(path):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise


def load_stations(municipios: pd.DataFrame) -> pd.DataFrame:
    """Tabla de referencia estación -> municipio (catálogo IDEAM, versión del repositorio).

    El municipio se asigna por coincidencia de NOMBRE del catálogo con el nombre DANE (más 3 mapeos manuales
    documentados). No hay geometrías municipales: la ubicación dentro del polígono NO se verifica.
    """
    st = read_csv_any(C.REF_DIR / "estaciones_candidatas_ideam.csv")
    dn = {nz(r.municipio): r.codigo_municipio for r in municipios.itertuples()}
    st["codigo_municipio"] = st["municipio"].map(lambda m: dn.get(nz(m)) or MANUAL_NAME_MAP.get(nz(m)))
    return st


def read_daily(var: str, code: int, folder: str):
    """Serie diaria (fecha -> valor). Devuelve (Serie, info). No corrige duplicados: informa y conserva el primero."""
    p = C.SOURCE_DIR / folder / f"{var}@{code}.data"
    if not p.exists():
        return None, None
    d = pd.read_csv(p, sep="|", dtype={"Fecha": str})
    d["fecha"] = pd.to_datetime(d["Fecha"].str[:10], errors="coerce")
    d["valor"] = pd.to_numeric(d["Valor"], errors="coerce")
    info = dict(archivo=p.name, filas=len(d), fechas_duplicadas=int(d["fecha"].duplicated().sum()),
                fechas_invalidas=int(d["fecha"].isna().sum()), valores_no_numericos=int(d["valor"].isna().sum()))
    d = d.dropna(subset=["fecha", "valor"]).drop_duplicates("fecha")
    return d.set_index("fecha")["valor"], info


def verified_calendar() -> pd.DataFrame:
    """Calendario SOLO para años verificados. SE1..SE52 domingo-sábado, anclado hacia atrás desde SE52 (25-31 dic)."""
    rows = []
    for y, end in C.SE52_END.items():
        end_d = date.fromisoformat(end)                      # sábado de la SE52 (oficial en el boletín)
        n = C.WEEKS_IN_YEAR[y]
        start52 = end_d - timedelta(days=6)
        for w in range(1, n + 1):
            s = start52 - timedelta(days=7 * (n - w))
            rows.append(dict(anio=y, semana_epidemiologica=w, semana_inicio=s.isoformat(),
                             semana_fin=(s + timedelta(days=6)).isoformat(), calendar_verificado="SI",
                             calendar_fuente=C.CALENDAR_VERIFIED[y]))
    return pd.DataFrame(rows)


def week_of_date_map(cal: pd.DataFrame) -> pd.DataFrame:
    """Una fila por día cubierto por el calendario verificado."""
    out = []
    for r in cal.itertuples():
        for k in range(7):
            out.append((pd.Timestamp(r.semana_inicio) + pd.Timedelta(days=k), r.anio, r.semana_epidemiologica))
    return pd.DataFrame(out, columns=["fecha", "anio", "semana_epidemiologica"])


def weekly_stats(series: pd.Series, daymap: pd.DataFrame, how: str) -> pd.DataFrame:
    """Estadística semanal (min / max / mean / sum) usando solo días válidos; n_dias sin imputar."""
    m = daymap.merge(series.rename("v"), left_on="fecha", right_index=True, how="left")
    g = m.groupby(["anio", "semana_epidemiologica"])["v"]
    out = pd.DataFrame({"n_dias": g.count()})
    out["valor"] = g.agg({"min": "min", "max": "max", "mean": "mean", "sum": "sum"}[how])
    return out.reset_index()
