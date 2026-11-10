"""Servicio de predicción: carga una sola vez los modelos entrenados y el dataset real, y responde por municipio y semana.

Nada se entrena ni se imputa aquí. Las variables faltantes llegan al modelo como NA (que HistGradientBoosting trata de forma
nativa) y se informan como advertencias. Los modelos se sirven tal como fueron evaluados (entrenados con 2012-2019).
"""
from __future__ import annotations

import json
import logging
import math
from datetime import timedelta
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from app.ml.common import (ARTIFACT_DIR, CHANNEL_FILE, DATA_DIR, DISCLAIMER, HORIZONS, MODEL_SPECS, SIGNAL_FEATURES, SIGNAL_FILE,
                           ChannelTable, add_channel_features, classify_trend, epi_week_of, load_dataset, municipality_sets,
                           reference_level, scale_ref)

logger = logging.getLogger(__name__)
DEFAULT_MODEL = "base_global"
SERVED_MODELS = ["base_global", "modelo_a", "modelo_b"]
LOW_VOLUME_MEDIAN = 10
HISTORY_WEEKS = 104


class ForecastUnavailable(Exception):
    """La predicción solicitada no se puede generar; el mensaje explica el motivo."""

    def __init__(self, code: str, message: str, status: int = 404):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _num(value) -> float | None:
    return None if value is None or (isinstance(value, float) and not math.isfinite(value)) or pd.isna(value) else float(value)
