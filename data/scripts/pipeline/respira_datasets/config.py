"""Configuración central del pipeline RESPIRA V1/V2/V3 (rutas, parámetros y reglas aprobadas).

Todas las decisiones metodológicas aprobadas viven aquí como parámetros versionados, no como constantes
escondidas en el código. Las fuentes originales se leen en modo solo lectura.
"""
from __future__ import annotations
import os
from pathlib import Path

PIPELINE_VERSION = "1.0.0"
CALENDAR_VERSION = "cal-v1-parcial-2016-2022"

REPO_ROOT = Path(__file__).resolve().parents[4]
# Los originales NO están en el repositorio (ver data/README.md); se leen de la copia local de datos.
SOURCE_DIR = Path(os.environ.get("RESPIRA_SOURCE_DIR", REPO_ROOT.parent / "RESPIRA - copia" / "data"))
INTERIM_DIR = REPO_ROOT / "data" / "interim"          # intermedios regenerables (ignorados por git)
OUT_DIR = REPO_ROOT / "data" / "processed"            # derivados (nunca dentro de los originales)
REF_DIR = REPO_ROOT / "reports"

YEARS = list(range(2012, 2023))
EVENT_CODE = "995"
SIV_SHEET = {2012: "995 52", 2013: "Hoja1", 2014: "Hoja1", 2015: "Hoja1", 2016: "Hoja1", 2017: "EVENTO 995",
             2018: "Hoja1", 2019: "Final", 2020: "995_2020_Depurada", 2021: "ACUMULADO", 2022: "995"}
# Campos SIVIGILA no personales que se extraen (se excluyen diligencia, cargo, telefono, correo, nit_upgd, nom_upgd).
SIV_KEEP = ["cod_eve", "fec_not", "semana", "ano", "cod_pre", "cod_sub", "cod_mun", "num_con",
            "iracext_1", "iracext_2", "iracext_3", "tot_iraext", "totcext_1", "totcext_2", "totcext_3", "tot_exturg",
            "ajuste", "fec_aju", "ndep_notif", "nmun_notif", "cod_dep"]

# Semanas por año epidemiológico presentes en SIVIGILA (semana 53 solo en 2014 y 2020). Es la malla de referencia:
# 64 x 574 = 36.736. NO es una verificación de calendario: solo 2016 y 2022 están verificados (ver CALENDAR_VERIFIED).
WEEKS_IN_YEAR = {y: (53 if y in (2014, 2020) else 52) for y in YEARS}
# Años con calendario epidemiológico verificado (boletines INS SE52, auditoría del calendario). Los demás NO.
CALENDAR_VERIFIED = {2016: "boletin INS SE52 2016 (25-31 dic)", 2022: "boletin INS SE52 2022 (25-31 dic)"}
SE52_END = {2016: "2016-12-31", 2022: "2022-12-31"}      # ancla oficial documentada


def regimen(year: int) -> str:
    return "PRE_PANDEMIA" if year <= 2019 else ("PANDEMIA" if year <= 2021 else "POST_PANDEMIA")


# Temperatura / precipitación
TEMP_MIN_DAYS = 6
PREC_MIN_DAYS = 7
STATION_MIN_WEEK_COVERAGE = 80.0   # % de semanas con >=6/7 días, estación en el mismo municipio
TEMP_VARS = {"temperatura_min": "TSSM_MN_D", "temperatura_max": "TSSM_MX_D", "temperatura_media": "TSSM_MEDIA_D"}
PREC_VAR = "PTPM_CON_INTER"
ALDANA_STATION = 52055230
CHACHAGUI_MUN = "52240"
CHACHAGUI_STATION = 52045020

# Horizontes y rezagos (preparación supervisada, sin entrenamiento)
LAGS = [1, 2, 3, 4]
HORIZONS = [2, 3]
