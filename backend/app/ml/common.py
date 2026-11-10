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
