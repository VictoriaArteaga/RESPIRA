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


def _trend_scores(y: np.ndarray, p: np.ndarray, ref: np.ndarray) -> dict:
    obs = np.array([classify_trend(a, b) for a, b in zip(y, ref)])
    pred = np.array([classify_trend(a, b) for a, b in zip(p, ref)])
    up_obs, up_pred = obs == "aumento", pred == "aumento"
    tp = int((up_obs & up_pred).sum())
    return {"exactitud_tendencia": float((obs == pred).mean()),
            "aumento_precision": tp / up_pred.sum() if up_pred.sum() else None,
            "aumento_recall": tp / up_obs.sum() if up_obs.sum() else None,
            "n_aumentos_observados": int(up_obs.sum())}


def _split_report(frame: pd.DataFrame, target: str, model_pred: np.ndarray, interval: tuple[float, float]) -> dict:
    y = frame[target].to_numpy(dtype=float)
    persist = frame["ira_0_4"].to_numpy(dtype=float)
    media4 = reference_level(frame).to_numpy(dtype=float)
    out = {"n": int(len(frame)), "modelo": _errors(y, model_pred), "persistencia": _errors(y, persist),
           "media_4_semanas": _errors(y, media4)}
    out["mejora_mae_vs_persistencia_pct"] = 100 * (1 - out["modelo"]["mae"] / out["persistencia"]["mae"])
    out.update(_trend_scores(y, model_pred, media4))
    lo = np.clip(model_pred + interval[0] * np.sqrt(model_pred + 1), 0, None)
    hi = model_pred + interval[1] * np.sqrt(model_pred + 1)
    out["cobertura_intervalo_80"] = float(((y >= lo) & (y <= hi)).mean())
    return out


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _levels(p: np.ndarray, t_mid: float, t_high: float) -> np.ndarray:
    return np.where(p >= t_high, "alta", np.where(p >= t_mid, "media", "baja"))


def _signal_report(y: np.ndarray, p: np.ndarray, t_mid: float, t_high: float) -> dict:
    lv = _levels(p, t_mid, t_high)
    by_level = {}
    for name in ("baja", "media", "alta"):
        m = lv == name
        by_level[name] = {"n": int(m.sum()), "proporcion_semanas": float(m.mean()),
                          "tasa_aumento_observada": float(y[m].mean()) if m.any() else None}
    hi = lv == "alta"
    return {"n": int(len(y)), "prevalencia_aumento": float(y.mean()), "auc": float(roc_auc_score(y, p)),
            "precision_promedio": float(average_precision_score(y, p)), "brier": float(brier_score_loss(y, p)),
            "alerta_alta": {"precision": float(y[hi].mean()) if hi.any() else None, "recall": float((hi & (y == 1)).sum() / max((y == 1).sum(), 1))},
            "por_nivel": by_level}


def train_increase_signal(df: pd.DataFrame, artifact_dir, verbose: bool = True) -> dict:
    """Clasificador de 'aumento' (>=20% y >=2 atenciones sobre el promedio de las últimas 4 semanas) a t+2 y t+3.
    Mismo protocolo temporal que los modelos de conteo. Niveles por cuantiles de la validación: alta = top (1 - prevalencia)."""
    ref = reference_level(df)
    out: dict = {"definicion": "aumento = predicción >=20% y >=2 atenciones sobre el promedio de las últimas 4 semanas",
                 "variables": SIGNAL_FEATURES, "horizontes": {}}
    for h in HORIZONS:
        target = f"objetivo_ira_t_mas_{h}"
        valid = df["ira_0_4"].notna() & df[target].notna() & ref.notna()
        data = df[valid].copy()
        data["y"] = [1 if classify_trend(a, b) == "aumento" else 0 for a, b in zip(data[target], reference_level(data))]
        tr, va = data[data["split_sugerido"] == "TRAIN"], data[data["split_sugerido"] == "VALIDACION"]

        def fit(frame, params):
            return HistGradientBoostingClassifier(early_stopping=False, random_state=SEED, **params).fit(frame[SIGNAL_FEATURES], frame["y"])

        scored = []
        for params in PARAM_GRID:
            m = fit(tr, params)
            scored.append((float(roc_auc_score(va["y"], m.predict_proba(va[SIGNAL_FEATURES])[:, 1])), params, m))
        val_auc, best, m_train = max(scored, key=lambda s: s[0])
        pv = m_train.predict_proba(va[SIGNAL_FEATURES])[:, 1]
        t_high, t_mid = float(np.quantile(pv, 1 - va["y"].mean())), float(np.quantile(pv, 0.5))
        final = fit(data[data["split_sugerido"].isin(["TRAIN", "VALIDACION"])], best)
        report = {"parametros": best, "umbral_medio": t_mid, "umbral_alto": t_high, "auc_validacion_candidatas": [round(s[0], 4) for s in scored],
                  "validacion_2019": _signal_report(va["y"].to_numpy(), pv, t_mid, t_high)}
        for name, split, model in (("prueba_2022", "TEST", final), ("pandemia_2020_2021", "PANDEMIA_ANALIZAR_APARTE", final)):
            part = data[data["split_sugerido"] == split]
            report[name] = _signal_report(part["y"].to_numpy(), model.predict_proba(part[SIGNAL_FEATURES])[:, 1], t_mid, t_high)
        out["horizontes"][str(h)] = report
        joblib.dump({"model": final, "features": SIGNAL_FEATURES, "horizon": h, "umbral_medio": t_mid, "umbral_alto": t_high,
                     "tasas_prueba_2022": {k: v["tasa_aumento_observada"] for k, v in report["prueba_2022"]["por_nivel"].items()},
                     "prevalencia_prueba_2022": report["prueba_2022"]["prevalencia_aumento"], "scikit_learn": sklearn.__version__},
                    artifact_dir / SIGNAL_FILE.format(h=h), compress=3)
        if verbose:
            t = report["prueba_2022"]
            print(f"senal_aumento h{h}: AUC val={val_auc:.3f} prueba={t['auc']:.3f} | alta: precisión={t['alerta_alta']['precision']:.2f} "
                  f"recall={t['alerta_alta']['recall']:.2f} (prevalencia {t['prevalencia_aumento']:.2f})", flush=True)
    return out
