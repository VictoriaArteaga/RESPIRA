"""Tablas supervisadas CANDIDATAS (sin entrenar nada): rezagos 1-4 y objetivos t+2 / t+3.

Reglas:
 * Rezagos y objetivos se desplazan por posición en la malla municipio-semana, pero solo se calculan si el
   desplazamiento no cruza una transición de año cuya secuencia no esté validada. Una transición Y -> Y+1 se
   considera validada únicamente si Y tiene calendario verificado (se conoce con evidencia la última semana de Y).
   Dentro de un mismo año la secuencia 1..N es consecutiva por definición.
 * Si el valor fuente es NULL (ausente / vacíos / no determinable) el rezago o el objetivo queda NULL con motivo.
 * Un rezago usa solo semanas <= t; el objetivo usa solo semanas > t. No se usa información posterior a t como predictor.
 * Las variantes SUMA y ULTIMO_REPORTE se mantienen en tablas separadas (escenarios de sensibilidad, no predictores simultáneos).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config as C

VARIANTS = {
    "SUMA": ("iracext_0_4_notificado_suma", "estado_dato_ira"),
    "ULTIMO_REPORTE": ("iracext_0_4_notificado_ultimo_reporte", "estado_dato_ira_ultimo_reporte"),
}


def _positions() -> pd.DataFrame:
    seq = [(y, w) for y in C.YEARS for w in range(1, C.WEEKS_IN_YEAR[y] + 1)]
    return pd.DataFrame(seq, columns=["anio", "semana_epidemiologica"]).assign(pos=range(len(seq)))


def offset_validity(k: int) -> np.ndarray:
    """Para cada posición i: motivo de validez del desplazamiento k (0 = válido)."""
    P = _positions()
    n = len(P)
    yrs = P["anio"].to_numpy()
    out = np.array(["OK"] * n, dtype=object)
    for i in range(n):
        j = i + k
        if j < 0 or j >= n:
            out[i] = "FUERA_DE_RANGO"
            continue
        lo, hi = sorted((yrs[i], yrs[j]))
        for y in range(lo, hi):               # transiciones y -> y+1 cruzadas
            if y not in C.CALENDAR_VERIFIED:
                out[i] = "TRANSICION_ANIO_NO_VALIDADA"
                break
    return out


def _shift(v: pd.DataFrame, col: str, estado_col: str, k: int) -> tuple[pd.Series, pd.Series]:
    """Valor y motivo del desplazamiento k (k<0 = rezago, k>0 = futuro) dentro de cada municipio."""
    n = len(_positions())
    val = v.groupby("codigo_municipio", sort=False)[col].shift(-k)           # shift(-k): valor en la posición t+k
    est = v.groupby("codigo_municipio", sort=False)[estado_col].shift(-k)
    validity = offset_validity(k)[v["posicion_secuencial"].to_numpy()]
    motivo = pd.Series(validity, index=v.index, dtype=object)
    ok = motivo.eq("OK")
    motivo[ok & val.isna()] = est[ok & val.isna()].map(
        lambda e: {"AUSENTE": "FUENTE_AUSENTE", "PARCIAL_VACIOS": "FUENTE_PARCIAL_VACIOS",
                   "NO_DETERMINABLE": "FUENTE_NO_DETERMINABLE"}.get(e, "FUENTE_NULA"))
    val = val.where(ok)
    return val, motivo


def build(v: pd.DataFrame, variant: str, horizon: int, temp: bool = False) -> pd.DataFrame:
    col, estado_col = VARIANTS[variant]
    d = v.sort_values(["codigo_municipio", "anio", "semana_epidemiologica"]).reset_index(drop=True)
    pos = _positions().set_index(["anio", "semana_epidemiologica"])["pos"]
    d["posicion_secuencial"] = pd.MultiIndex.from_frame(d[["anio", "semana_epidemiologica"]]).map(pos).astype(int)
    out = d[["codigo_municipio", "municipio", "anio", "semana_epidemiologica", "regimen", "calendar_verificado",
             "completitud_no_verificada", "posicion_secuencial"]].copy()
    out["interpretacion_reportes"] = variant
    out["horizonte_semanas"] = horizon
    out["ira_t"] = d[col]
    out["estado_ira_t"] = d[estado_col]
    motivos = []
    for k in C.LAGS:
        val, mot = _shift(d, col, estado_col, -k)
        out[f"ira_lag{k}"] = val
        motivos.append(mot.where(mot != "OK", ""))
    out["motivo_rezagos_nulos"] = [";".join(f"lag{k}:{m}" for k, m in zip(C.LAGS, row) if m) for row in zip(*motivos)]
    tv, tm = _shift(d, col, estado_col, horizon)
    out[f"target_ira_t_plus_{horizon}"] = tv
    out["motivo_target_nulo"] = tm.where(tm != "OK", "")
    tgt_pos = (d["posicion_secuencial"] + horizon).clip(upper=len(_positions()) - 1)
    P = _positions().set_index("pos")
    out["anio_objetivo"] = tgt_pos.map(P["anio"]).where(tm.eq("OK") | tm.str.startswith("FUENTE"))
    out["semana_objetivo"] = tgt_pos.map(P["semana_epidemiologica"]).where(out["anio_objetivo"].notna())
    out["poblacion_menor_5"] = d["poblacion_menor_5"]
    out["dane_libro"] = d["dane_libro"]
    out["tiene_reportes_repetidos"] = d["tiene_reportes_repetidos"]
    out["tiene_codigo_territorial_incongruente"] = d["tiene_codigo_territorial_incongruente"]
    if temp:
        for k_ in C.TEMP_VARS:
            out[f"{k_}_semanal_t"] = d[f"{k_}_semanal"]
        out["estado_calidad_temperatura_t"] = d["estado_calidad_temperatura"]
        for k in C.LAGS:
            val, mot = _shift(d, "temperatura_media_semanal", "estado_calidad_temperatura", -k)
            out[f"temperatura_media_lag{k}"] = val
        out["temperatura_disponible_t"] = d["estado_calidad_temperatura"].eq("VALIDO")
    lagcols = [f"ira_lag{k}" for k in C.LAGS]
    out["fila_completa_ira"] = out[["ira_t", *lagcols, f"target_ira_t_plus_{horizon}"]].notna().all(axis=1)
    out["habilitado_entrenamiento"] = False
    out["motivo_no_habilitado"] = ("INDICADOR_Y_REPORTES_REPETIDOS_PENDIENTES_INS;CALENDARIO_NO_VERIFICADO_EN_TODOS_LOS_ANIOS_EXCEPTO_2016_Y_2022"
                                   + ";COMPLETITUD_2021_NO_VERIFICADA")
    if temp:
        out["motivo_no_habilitado"] += ";TEMPERATURA_SOLO_EN_ANIOS_CON_CALENDARIO_VERIFICADO;REPRESENTATIVIDAD_ESTACION_NO_VALIDADA"
    return out
