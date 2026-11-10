"""Entrenamiento y evaluación de los modelos de predicción de IRA (t+2 y t+3).

Algoritmo: HistGradientBoostingRegressor (scikit-learn): rápido, reproducible (semilla fija, sin early stopping aleatorio)
y admite valores faltantes de forma nativa, de modo que NO se imputa nada. Se predice la razón entre el valor futuro y el nivel
reciente (media de 4 semanas + 1), ponderada por ese nivel, y se multiplica de nuevo: así un solo modelo sirve a municipios de
escalas muy distintas (Pasto ~340/semana frente a ~2/semana en los pequeños).

Protocolo temporal (columna split_sugerido del dataset):
  1. Se ajusta con 2012-2018 y se elige la configuración con menor MAE en 2019 (validación).
  2. Se reajusta con 2012-2019 con la configuración elegida. Ese es el modelo que se guarda y se sirve.
  3. 2022 (prueba) y 2020-2021 (pandemia, aparte) NO participan en ningún ajuste.
Todas las variables de entrada se calculan con datos hasta la semana t; el objetivo es el valor en t+2 o t+3.
"""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from app.ml.common import (ARTIFACT_DIR, CHANNEL_FEATURES, CHANNEL_FILE, DATASET_PATH, HORIZONS, MODEL_SPECS, SEED, SIGNAL_FEATURES,
                           SIGNAL_FILE, ChannelTable, add_channel_features, classify_trend, load_dataset, municipality_sets,
                           reference_level, scale_ref)

PARAM_GRID = [
    dict(max_iter=200, learning_rate=0.05, max_depth=4, min_samples_leaf=40),
    dict(max_iter=300, learning_rate=0.03, max_depth=3, min_samples_leaf=60, l2_regularization=1.0),
    dict(max_iter=400, learning_rate=0.03, max_depth=6, min_samples_leaf=20, l2_regularization=1.0),
]
SPLITS = {"validacion_2019": "VALIDACION", "prueba_2022": "TEST", "pandemia_2020_2021": "PANDEMIA_ANALIZAR_APARTE"}


def _fit(frame: pd.DataFrame, features: list[str], target: str, params: dict) -> HistGradientBoostingRegressor:
    model = HistGradientBoostingRegressor(loss="squared_error", early_stopping=False, random_state=SEED, **params)
    ref = scale_ref(frame)
    model.fit(frame[features], frame[target] / ref, sample_weight=ref)
    return model


def predict(model, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    return np.clip(model.predict(frame[features]) * scale_ref(frame).to_numpy(), 0.0, None)


def _errors(y: np.ndarray, p: np.ndarray) -> dict:
    err = p - y
    return {"mae": float(np.mean(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2))),
            "wape": float(np.abs(err).sum() / y.sum()) if y.sum() > 0 else None, "sesgo": float(err.mean())}
