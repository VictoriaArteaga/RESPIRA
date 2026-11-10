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

    @staticmethod
    def _load_extension() -> dict | None:
        """Datos públicos 2023-2025 adjuntos al dataset (no se usan para entrenar: falta la IRA de esos años)."""
        path = DATA_DIR / "extension_2023_2025_manifest.json"
        if not path.exists():
            return None
        m = json.loads(path.read_text(encoding="utf-8"))
        return {"ira_last_week": {"year": 2022, "week": 52}, "ira_public_2023_2025": bool(m["ira_disponible_2023_2025"]),
                "population_through_year": 2025, "calendar_weeks": m["calendario"]["semanas"],
                "calendar_ins_anchors": m["calendario"]["anclas_ins_verificadas"],
                "climate_public": {k: {"municipalities": v["municipios_con_estacion_publica"], "valid_municipality_weeks": v["semanas_validas_total"]}
                                   for k, v in m["clima_publico"].items()},
                "used_for_training": False,
                "note": "El evento 995 de SIVIGILA de 2023-2025 no es público: los modelos se entrenan y evalúan hasta 2022. "
                        "El clima, la población y el calendario de 2023-2025 quedan adjuntos para cuando se obtenga la IRA."}

    # ------------------------------------------------------------------ catálogo
    def available_models(self, code: str) -> list[str]:
        out = ["base_global"]
        if code in self.sets["precipitacion"]:
            out.append("modelo_a")
        if code in self.sets["temperatura"]:
            out.append("modelo_b")
        return out

    def _last_observed(self, g: pd.DataFrame) -> pd.Series | None:
        seen = g[g["ira_0_4"].notna()]
        return seen.iloc[-1] if len(seen) else None

    def list_municipalities(self) -> list[dict]:
        rows = []
        for code, g in self._by_mun.items():
            last = self._last_observed(g)
            median = _num(self._median.get(code))
            rows.append({
                "divipola_code": code, "name": self.names[code],
                "available_models": self.available_models(code), "default_model": DEFAULT_MODEL,
                "has_precipitation": code in self.sets["precipitacion"], "has_temperature": code in self.sets["temperatura"],
                "observed_weeks_pct": round(100 * float(g["ira_0_4"].notna().mean()), 1),
                "last_observed": None if last is None else {"year": int(last["anio"]), "week": int(last["semana_epidemiologica"])},
                "median_weekly_cases_2012_2019": median,
                "low_volume": bool(median is not None and median < LOW_VOLUME_MEDIAN),
            })
        return sorted(rows, key=lambda r: r["name"])

    def _signal_block(self, h: int) -> dict | None:
        rep = self.metrics.get("senal_aumento", {}).get("horizontes", {}).get(str(h))
        if not rep:
            return None
        def pack(key):
            r = rep[key]
            return {"n": r["n"], "increase_prevalence": r["prevalencia_aumento"], "auc": r["auc"], "average_precision": r["precision_promedio"],
                    "high_precision": r["alerta_alta"]["precision"], "high_recall": r["alerta_alta"]["recall"],
                    "rate_by_level": {k: v["tasa_aumento_observada"] for k, v in r["por_nivel"].items()},
                    "share_by_level": {k: v["proporcion_semanas"] for k, v in r["por_nivel"].items()}}
        return {"validation_2019": pack("validacion_2019"), "test_2022": pack("prueba_2022"), "pandemic_2020_2021": pack("pandemia_2020_2021")}

    def _channel_block(self, h: int) -> dict | None:
        rep = self.metrics.get("canal_endemico", {}).get("horizontes", {}).get(str(h))
        if not rep:
            return None

        def pack(kind: str, key: str) -> dict:
            r = rep[kind][key]
            return {"n": r["n"], "exceed_prevalence": r["prevalencia_aumento"], "auc": r["auc"], "auc_simple_rule": r.get("auc_regla_simple"),
                    "high_precision": r["alerta_alta"]["precision"], "high_recall": r["alerta_alta"]["recall"],
                    "rate_by_level": {k: v["tasa_aumento_observada"] for k, v in r["por_nivel"].items()}}
        return {kind: {"validation_2019": pack(kind, "validacion_2019"), "test_2022": pack(kind, "prueba_2022"),
                       "pandemic_2020_2021": pack(kind, "pandemia_2020_2021")} for kind in ("p75", "p90")}

    @staticmethod
    def _zone(cases: float | None, p75: float, p90: float) -> str | None:
        if cases is None:
            return None
        return "alerta" if cases > p90 else "sobre" if cases > p75 else "dentro"

    def _channel_outlook(self, row: pd.Series, predictions: list[dict]) -> list[dict]:
        """Zona esperada del canal endémico de la semana objetivo: posición del conteo predicho y probabilidad de superar P75 / P90."""
        out = []
        frame_src = row.to_frame().T.infer_objects()
        for pred in predictions:
            h = pred["horizon_weeks"]
            f = add_channel_features(frame_src, self.channels, h)
            r = f.iloc[0]
            item = {"horizon_weeks": h, "target_year": pred["target_year"], "target_week": pred["target_week"]}
            if pd.isna(r["p75_t"]):
                item.update({"available": False, "reason": "Menos de 3 años anteriores con dato para esa semana: no hay canal endémico."})
                out.append(item)
                continue
            p75, p90 = float(r["p75_t"]), float(r["p90_t"])
            item.update({"available": True, "channel": {"p25": round(float(r["p25_t"]), 1), "p50": round(float(r["p50_t"]), 1),
                                                        "p75": round(p75, 1), "p90": round(p90, 1)},
                         "predicted_zone": self._zone(pred["predicted_cases"], p75, p90),
                         "observed_zone": self._zone(pred["observed_cases"], p75, p90)})
            for kind in ("p75", "p90"):
                art = self.channel_models.get((kind, h))
                if art is None:
                    continue
                X = f[art["features"]].astype(float)
                prob = float(art["model"].predict_proba(X)[:1][0, 1])
                level = "alta" if prob >= art["umbral_alto"] else "media" if prob >= art["umbral_medio"] else "baja"
                item[f"exceed_{kind}"] = {"probability": round(prob, 3), "level": level,
                                          "historical_rate_for_level": art["tasas_prueba_2022"][level],
                                          "base_rate": art["prevalencia_prueba_2022"]}
            out.append(item)
        return out

    def _signal_for(self, row: pd.Series, h: int, reference: float | None) -> dict | None:
        art = self.signal.get(h)
        if art is None:
            return None
        X = pd.DataFrame([row[art["features"]].astype(float)])
        p = float(art["model"].predict_proba(X)[0, 1])
        level = "alta" if p >= art["umbral_alto"] else "media" if p >= art["umbral_medio"] else "baja"
        observed = _num(row.get(f"objetivo_ira_t_mas_{h}"))
        return {"horizon_weeks": h, "probability": round(p, 3), "level": level,
                "historical_increase_rate_for_level": art["tasas_prueba_2022"][level],
                "base_increase_rate": art["prevalencia_prueba_2022"],
                "observed_increase": None if observed is None or reference is None else classify_trend(observed, reference) == "aumento"}
