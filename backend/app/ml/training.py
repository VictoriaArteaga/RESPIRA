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


def train_channel_signals(df: pd.DataFrame, artifact_dir, verbose: bool = True) -> dict:
    """Probabilidad de que las atenciones de t+h superen el percentil 75 (sobre lo esperado) o el 90 (zona de alerta) del canal
    endémico de esa semana. Canal = misma semana de años anteriores (sin pandemia). Mismo protocolo temporal."""
    table = ChannelTable(df)
    feats = SIGNAL_FEATURES + CHANNEL_FEATURES
    out: dict = {"definicion": "supera el percentil 75 / 90 del canal endémico de la semana objetivo (años anteriores, sin 2020-2021)",
                 "variables": feats, "horizontes": {}}
    for h in HORIZONS:
        target = f"objetivo_ira_t_mas_{h}"
        d = add_channel_features(df, table, h)
        d = d[d["ira_0_4"].notna() & d[target].notna() & d["p75_t"].notna()].copy()
        out["horizontes"][str(h)] = {}
        for kind, col in (("p75", "p75_t"), ("p90", "p90_t")):
            d["y"] = (d[target] > d[col]).astype(int)
            tr, va = d[d["split_sugerido"] == "TRAIN"], d[d["split_sugerido"] == "VALIDACION"]

            def fit(frame, params):
                return HistGradientBoostingClassifier(early_stopping=False, random_state=SEED, **params).fit(frame[feats], frame["y"])

            scored = []
            for params in PARAM_GRID:
                m = fit(tr, params)
                scored.append((float(roc_auc_score(va["y"], m.predict_proba(va[feats])[:, 1])), params, m))
            val_auc, best, m_train = max(scored, key=lambda s: s[0])
            pv = m_train.predict_proba(va[feats])[:, 1]
            t_high, t_mid = float(np.quantile(pv, 1 - va["y"].mean())), float(np.quantile(pv, 0.5))
            final = fit(d[d["split_sugerido"].isin(["TRAIN", "VALIDACION"])], best)
            rep = {"parametros": best, "umbral_medio": t_mid, "umbral_alto": t_high,
                   "validacion_2019": _signal_report(va["y"].to_numpy(), pv, t_mid, t_high)}
            for name, split in (("prueba_2022", "TEST"), ("pandemia_2020_2021", "PANDEMIA_ANALIZAR_APARTE")):
                part = d[d["split_sugerido"] == split]
                rep[name] = _signal_report(part["y"].to_numpy(), final.predict_proba(part[feats])[:, 1], t_mid, t_high)
                simple = (part["ira_media_4s"].fillna(part["ira_0_4"]) / (part[col] + 1)).to_numpy()
                rep[name]["auc_regla_simple"] = float(roc_auc_score(part["y"], simple))   # promedio reciente / percentil, sin modelo
            out["horizontes"][str(h)][kind] = rep
            joblib.dump({"model": final, "features": feats, "horizon": h, "kind": kind, "umbral_medio": t_mid, "umbral_alto": t_high,
                         "tasas_prueba_2022": {k: v["tasa_aumento_observada"] for k, v in rep["prueba_2022"]["por_nivel"].items()},
                         "prevalencia_prueba_2022": rep["prueba_2022"]["prevalencia_aumento"], "scikit_learn": sklearn.__version__},
                        artifact_dir / CHANNEL_FILE.format(kind=kind, h=h), compress=3)
            if verbose:
                t = rep["prueba_2022"]
                print(f"canal_{kind} h{h}: AUC val={val_auc:.3f} prueba={t['auc']:.3f} (regla simple {t['auc_regla_simple']:.3f}) | "
                      f"alta: precisión={t['alerta_alta']['precision']:.2f} recall={t['alerta_alta']['recall']:.2f} (prevalencia {t['prevalencia_aumento']:.2f})", flush=True)
    return out


def train_all(dataset_path=DATASET_PATH, artifact_dir=ARTIFACT_DIR, verbose: bool = True) -> dict:
    df = load_dataset(dataset_path)
    sets = municipality_sets(df)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict = {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "dataset": {"archivo": str(dataset_path.name), "sha256": _sha256(dataset_path), "filas": int(len(df))},
                     "entorno": {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
                                 "semilla": SEED, "algoritmo": "HistGradientBoostingRegressor (razón al nivel reciente)"},
                     "protocolo": "ajuste 2012-2018 -> selección en 2019 -> reajuste 2012-2019 -> prueba 2022; pandemia 2020-2021 aparte",
                     "modelos": {}}
    by_mun_rows: list[dict] = []
    for model_id, spec in MODEL_SPECS.items():
        muni = sets[spec["municipios"]]
        features = spec["features"]
        entry = {"etiqueta": spec["etiqueta"], "grupo": spec["grupo"], "referencia": spec["referencia"],
                 "n_municipios": len(muni), "variables": features, "horizontes": {}}
        for h in HORIZONS:
            target = f"objetivo_ira_t_mas_{h}"
            data = df[df["codigo_divipola"].isin(muni) & df["ira_0_4"].notna() & df[target].notna()]
            train, val = data[data["split_sugerido"] == "TRAIN"], data[data["split_sugerido"] == "VALIDACION"]
            # 1) selección de configuración en 2019
            scored = []
            for params in PARAM_GRID:
                m = _fit(train, features, target, params)
                scored.append((float(np.mean(np.abs(predict(m, val, features) - val[target].to_numpy()))), params, m))
            val_mae, best_params, m_train = min(scored, key=lambda s: s[0])
            # intervalo empírico 80% con los residuos estandarizados de 2019 (modelo ajustado solo hasta 2018)
            p_val = predict(m_train, val, features)
            resid = (val[target].to_numpy() - p_val) / np.sqrt(p_val + 1)
            interval = (float(np.quantile(resid, 0.10)), float(np.quantile(resid, 0.90)))
            # 2) reajuste con 2012-2019 (modelo que se sirve)
            final = _fit(data[data["split_sugerido"].isin(["TRAIN", "VALIDACION"])], features, target, best_params)
            report = {"parametros": best_params, "filas_entrenamiento_final": int(data["split_sugerido"].isin(["TRAIN", "VALIDACION"]).sum()),
                      "mae_validacion_candidatas": [round(s[0], 4) for s in scored], "intervalo_residual_q10_q90": interval}
            for name, split in SPLITS.items():
                part = data[data["split_sugerido"] == split]
                if part.empty:
                    report[name] = None
                    continue
                model_for_split = m_train if split == "VALIDACION" else final   # validación: modelo ajustado hasta 2018
                p = predict(model_for_split, part, features)
                report[name] = _split_report(part, target, p, interval)
                if split in ("VALIDACION", "TEST"):
                    persist_p = part["ira_0_4"].to_numpy(dtype=float)
                    for code, g in part.assign(p=p).groupby("codigo_divipola"):
                        y = g[target].to_numpy(dtype=float)
                        by_mun_rows.append({"modelo": model_id, "horizonte": h, "periodo": name, "codigo_divipola": code,
                                            "municipio": g["municipio"].iloc[0], "n": len(g), "promedio_observado": round(float(y.mean()), 2),
                                            "mae_modelo": round(float(np.abs(g["p"] - y).mean()), 3),
                                            "mae_persistencia": round(float(np.abs(g["ira_0_4"] - y).mean()), 3)})
            entry["horizontes"][str(h)] = report
            joblib.dump({"model": final, "features": features, "horizon": h, "model_id": model_id, "parametros": best_params,
                         "interval": interval, "municipios": sorted(muni), "entrenado_hasta": "2019",
                         "scikit_learn": sklearn.__version__}, artifact_dir / f"{model_id}_h{h}.joblib", compress=3)
            if verbose:
                t = report["prueba_2022"]
                print(f"{model_id:12s} h{h}: n_mun={len(muni):2d} val_MAE={val_mae:.3f} | prueba 2022 n={t['n']} "
                      f"MAE modelo={t['modelo']['mae']:.3f} persistencia={t['persistencia']['mae']:.3f} "
                      f"mejora={t['mejora_mae_vs_persistencia_pct']:.1f}%", flush=True)
        metrics["modelos"][model_id] = entry
    # aporte de las variables climáticas frente al modelo base entrenado sobre los mismos municipios
    comp = []
    for model_id, spec in MODEL_SPECS.items():
        if not spec["referencia"]:
            continue
        for h in HORIZONS:
            for period in ("validacion_2019", "prueba_2022", "pandemia_2020_2021"):
                a = metrics["modelos"][model_id]["horizontes"][str(h)][period]
                b = metrics["modelos"][spec["referencia"]]["horizontes"][str(h)][period]
                if a and b:
                    comp.append({"modelo": model_id, "base": spec["referencia"], "horizonte": h, "periodo": period, "n": a["n"],
                                 "mae_con_clima": a["modelo"]["mae"], "mae_base": b["modelo"]["mae"],
                                 "rmse_con_clima": a["modelo"]["rmse"], "rmse_base": b["modelo"]["rmse"],
                                 "mejora_mae_pct": 100 * (1 - a["modelo"]["mae"] / b["modelo"]["mae"])})
    metrics["aporte_variables_climaticas"] = comp
    metrics["senal_aumento"] = train_increase_signal(df, artifact_dir, verbose)
    metrics["canal_endemico"] = train_channel_signals(df, artifact_dir, verbose)
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(by_mun_rows).to_csv(artifact_dir / "metrics_by_municipality.csv", index=False, encoding="utf-8-sig")
    return metrics
