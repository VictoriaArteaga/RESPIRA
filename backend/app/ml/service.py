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


class ForecastService:
    def __init__(self, artifact_dir=ARTIFACT_DIR) -> None:
        self.artifact_dir = artifact_dir
        self.df = load_dataset()
        self.sets = municipality_sets(self.df)
        self.metrics: dict = json.loads((artifact_dir / "metrics.json").read_text(encoding="utf-8"))
        self.models: dict[tuple[str, int], dict] = {}
        for model_id in SERVED_MODELS:
            for h in HORIZONS:
                path = artifact_dir / f"{model_id}_h{h}.joblib"
                if not path.exists():
                    raise FileNotFoundError(f"Falta el modelo entrenado {path.name}. Ejecute scripts/train_forecast.py")
                self.models[(model_id, h)] = joblib.load(path)
        self.signal: dict[int, dict] = {}
        for h in HORIZONS:
            path = artifact_dir / SIGNAL_FILE.format(h=h)
            if path.exists():
                self.signal[h] = joblib.load(path)
        self.channel_models: dict[tuple[str, int], dict] = {}
        for h in HORIZONS:
            for kind in ("p75", "p90"):
                path = artifact_dir / CHANNEL_FILE.format(kind=kind, h=h)
                if path.exists():
                    self.channel_models[(kind, h)] = joblib.load(path)
        self.channels = ChannelTable(self.df)
        self.extension = self._load_extension()
        self.names = self.df.drop_duplicates("codigo_divipola").set_index("codigo_divipola")["municipio"].to_dict()
        self._median = self.df[self.df["anio"] <= 2019].groupby("codigo_divipola")["ira_0_4"].median()
        self._by_mun = {code: g.reset_index(drop=True) for code, g in self.df.groupby("codigo_divipola")}
