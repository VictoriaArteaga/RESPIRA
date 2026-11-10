"""Constantes y utilidades compartidas por el entrenamiento y el servicio de predicción de RESPIRA.

La IA predice atenciones por IRA notificadas (SIVIGILA 995, menores de 5 años) por municipio a 2 y 3 semanas.
Es una predicción EXPERIMENTAL de la demo: no es diagnóstico, ni confirmación de brote, ni alerta sanitaria oficial.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("RESPIRA_V2_DATA_DIR", REPO_ROOT / "data" / "respira_v2"))
DATASET_PATH = DATA_DIR / "dataset_entrenamiento.csv"
ARTIFACT_DIR = Path(os.environ.get("RESPIRA_ML_DIR", REPO_ROOT / "backend" / "ml_artifacts"))
SEED = 0
HORIZONS = (2, 3)

# ---- variables por grupo (todas calculadas con información disponible hasta la semana t)
BASE_FEATURES = ["ira_0_4", "ira_lag1", "ira_lag2", "ira_lag3", "ira_lag4", "ira_media_4s", "ira_media_8s",
                 "ira_cambio_vs_lag1", "ira_52s_atras", "semana_sin", "semana_cos", "mes_aprox"]
PRECIP_FEATURES = ["precipitacion", "precipitacion_lag1", "precipitacion_lag2", "precipitacion_media_4s"]
TEMP_FEATURES = ["temp_media", "temp_min", "temp_max", "temp_media_lag1", "temp_media_lag2", "temp_media_media_4s"]

# Señal de aumento: historial de IRA + consultas totales (única variable extra que mejoró de forma consistente en validación y prueba).
CONSULT_FEATURES = ["cons", "cons_lag1", "cons_media_4s", "proporcion_ira_sobre_consultas", "proporcion_ira_lag1", "prop_media_4s"]
SIGNAL_FEATURES = BASE_FEATURES + CONSULT_FEATURES
SIGNAL_FILE = "senal_aumento_h{h}.joblib"

# Canal endémico: misma semana de años anteriores (sin pandemia), como el canal de la app (P25/P50/P75/P90).
PANDEMIC_YEARS = {2020, 2021}
CHANNEL_MIN_YEARS = 3
CHANNEL_FEATURES = ["p50_t", "p75_t", "p90_t", "ref_vs_p75", "ira_vs_p50", "spread", "pos_act"]
CHANNEL_FILE = "canal_{kind}_h{h}.joblib"   # kind: p75 | p90

# id -> definición. 'municipios' se deriva de los datos (qué municipios tienen la variable climática apta).
MODEL_SPECS: dict[str, dict] = {
    "base_global": dict(etiqueta="Base (solo historial de IRA) · todos los municipios", grupo="base", municipios="todos",
                        features=BASE_FEATURES, referencia=None),
    "base_a": dict(etiqueta="Base (solo historial de IRA) · municipios con precipitación", grupo="base", municipios="precipitacion",
                   features=BASE_FEATURES, referencia=None),
    "modelo_a": dict(etiqueta="Modelo A · historial de IRA + precipitación", grupo="clima", municipios="precipitacion",
                     features=BASE_FEATURES + PRECIP_FEATURES, referencia="base_a"),
    "base_b": dict(etiqueta="Base (solo historial de IRA) · municipios con temperatura", grupo="base", municipios="temperatura",
                   features=BASE_FEATURES, referencia=None),
    "modelo_b": dict(etiqueta="Modelo B · historial de IRA + precipitación + temperatura", grupo="clima", municipios="temperatura",
                     features=BASE_FEATURES + PRECIP_FEATURES + TEMP_FEATURES, referencia="base_b"),
}

DISCLAIMER = ("Predicción experimental de la demo de RESPIRA. No es un diagnóstico, no confirma un brote y no constituye "
              "una alerta sanitaria oficial. Estima atenciones por IRA notificadas, no casos ni incidencia.")

# ---- tendencia respecto al periodo de referencia (heurística de la demo, consistente con el umbral moderado de RiskService)
TREND_REL = 0.20      # ±20% respecto a la referencia
TREND_MIN_ABS = 2.0   # cambios menores a 2 atenciones se consideran estables (evita ruido en municipios pequeños)


def classify_trend(prediction: float, reference: float | None) -> str:
    """'aumento' | 'estable' | 'disminucion' | 'sin_referencia' respecto a la referencia (media de las últimas 4 semanas)."""
    if reference is None or not np.isfinite(reference):
        return "sin_referencia"
    diff = prediction - reference
    if abs(diff) < TREND_MIN_ABS:
        return "estable"
    rel = diff / reference if reference > 0 else np.inf
    return "aumento" if rel >= TREND_REL else "disminucion" if rel <= -TREND_REL else "estable"


def reference_level(df: pd.DataFrame) -> pd.Series:
    """Nivel reciente (media de 4 semanas; si falta, el valor actual). Solo usa información hasta t."""
    return df["ira_media_4s"].fillna(df["ira_0_4"])


def scale_ref(df: pd.DataFrame) -> pd.Series:
    return reference_level(df) + 1.0


# ---- calendario epidemiológico (regla de la SE1: contiene el 4 de enero; igual a data/scripts/respira_v2/03_calendario.py)
def _start_se1(year: int) -> date:
    j4 = date(year, 1, 4)
    return j4 - timedelta(days=(j4.weekday() + 1) % 7)


def epi_week_of(day: date) -> tuple[int, int]:
    for year in (day.year - 1, day.year, day.year + 1):
        if _start_se1(year) <= day < _start_se1(year + 1):
            return year, (day - _start_se1(year)).days // 7 + 1
    raise ValueError(day)


def add_signal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega variables de consultas totales (solo pasado y presente) para la señal de aumento. df debe venir ordenado."""
    out = df.copy()
    g = out.groupby("codigo_divipola", sort=False)
    out["cons"] = out["consultas_0_4_totales_ultimo_reporte"]
    out["cons_lag1"] = g["cons"].shift(1)
    out["cons_media_4s"] = out.groupby("codigo_divipola", sort=False)["cons"].transform(lambda x: x.rolling(4, min_periods=3).mean())
    out["prop_media_4s"] = out.groupby("codigo_divipola", sort=False)["proporcion_ira_sobre_consultas"].transform(
        lambda x: x.rolling(4, min_periods=3).mean())
    return out


class ChannelTable:
    """Percentiles de IRA de la misma semana epidemiológica en años ANTERIORES al año consultado (sin 2020-2021)."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._piv = {code: g.pivot_table(index="semana_epidemiologica", columns="anio", values="ira_0_4", aggfunc="first")
                     for code, g in df.groupby("codigo_divipola")}
        self._cache: dict[tuple, tuple] = {}

    def get(self, code: str, year: int, week: int) -> tuple[float, float, float, float]:
        key = (code, year, week)
        if key not in self._cache:
            t = self._piv.get(code)
            nan = (np.nan,) * 4
            if t is None or week not in t.index:
                self._cache[key] = nan
            else:
                v = t.loc[week, [y for y in t.columns if y < year and y not in PANDEMIC_YEARS]].dropna().to_numpy(dtype=float)
                self._cache[key] = nan if len(v) < CHANNEL_MIN_YEARS else tuple(float(x) for x in np.percentile(v, [25, 50, 75, 90]))
        return self._cache[key]
