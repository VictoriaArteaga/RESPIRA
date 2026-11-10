"""Construcción de V2 (temperatura) y V3 (precipitación candidata) a partir de V1.

Principios:
 * El vínculo IDEAM-SIVIGILA por semana solo se hace en años con calendario verificado (2016 y 2022).
 * Estación únicamente del mismo municipio (catálogo IDEAM); sin vecinas, sin interpolación, sin imputación.
 * Aldana (52055230): temperatura mín/máx/media excluidas -> SERIE_NO_CONFIABLE.
 * Chachagüí (52045020): ubicación dentro del municipio no demostrable con los datos -> SIN_ESTACION_VALIDADA.
 * Precipitación PTPM_CON_INTER: semántica/unidad pendientes -> no se suma ni se declara validada.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config as C, ideam

# Interruptor: solo se pondría True con confirmación escrita de IDEAM sobre PTPM_CON_INTER (significado y unidad).
PREC_SEMANTICS_CONFIRMED = False
PREC_UNIT_REPORTED = "mm (documentado para PTPM_CON; NO confirmado para el sufijo INTER)"
STATUS_SEM = "SEMANTICA_PENDIENTE_CONFIRMACION"


def _station_meta(st: pd.DataFrame) -> pd.DataFrame:
    return st.set_index("codigo_estacion")


def aldana_evidence() -> dict:
    """Recalcula la evidencia de la serie no confiable de Aldana (días con mín==máx y media>máx)."""
    s = {v: ideam.read_daily(v, C.ALDANA_STATION, ideam.TEMP_FOLDER)[0] for v in C.TEMP_VARS.values()}
    t = pd.concat([s["TSSM_MN_D"], s["TSSM_MX_D"], s["TSSM_MEDIA_D"]], axis=1, keys=["mn", "mx", "me"])
    t = t[(t.index >= "2012-01-01") & (t.index <= "2022-12-31")].dropna()
    return dict(dias_con_3_variables=int(len(t)), dias_min_igual_max=int((t.mn == t.mx).sum()),
                dias_media_mayor_max=int((t.me > t.mx + 1e-9).sum()), dias_min_mayor_max=int((t.mn > t.mx).sum()))


def chachagui_evidence(st: pd.DataFrame) -> dict:
    x = st[st["codigo_estacion"] == C.CHACHAGUI_STATION].iloc[0]
    others = st[(st["municipio"].map(ideam.nz) == "CHACHAGUI") & (st["codigo_estacion"] != C.CHACHAGUI_STATION)]
    return dict(codigo=int(x.codigo_estacion), nombre=x.nombre_estacion, municipio_catalogo=x.municipio,
                latitud=float(x.latitud), longitud=float(x.longitud), altitud=float(x.altitud),
                otras_estaciones_catalogadas_en_el_municipio=";".join(map(str, others.codigo_estacion)),
                limites_municipales_disponibles="NO", ubicacion_dentro_del_municipio_demostrada="NO")


# ----------------------------------------------------------------------------- temperatura (V2)
def weekly_station_temperature(code: int, daymap: pd.DataFrame):
    out = None
    infos = {}
    for key, var in C.TEMP_VARS.items():
        s, info = ideam.read_daily(var, code, ideam.TEMP_FOLDER)
        if s is None:
            return None, infos
        infos[var] = info
        how = {"temperatura_min": "min", "temperatura_max": "max", "temperatura_media": "mean"}[key]
        w = ideam.weekly_stats(s, daymap, how).rename(columns={"n_dias": f"n_dias_{key}", "valor": f"{key}_semanal"})
        out = w if out is None else out.merge(w, on=["anio", "semana_epidemiologica"])
    for key in C.TEMP_VARS:   # regla 6/7: valor solo si hay >= 6 días válidos; estadística solo con días válidos
        bad = out[f"n_dias_{key}"] < C.TEMP_MIN_DAYS
        out.loc[bad, f"{key}_semanal"] = np.nan
    out["n_dias_temperatura"] = out[[f"n_dias_{k}" for k in C.TEMP_VARS]].min(axis=1)
    return out, infos


def build_v2(v1: pd.DataFrame, st: pd.DataFrame, mun: pd.DataFrame, cal: pd.DataFrame):
    daymap = ideam.week_of_date_map(cal)
    nweeks_ver = len(cal)
    meta = _station_meta(st)
    ald = aldana_evidence()
    cha = chachagui_evidence(st)
    # ---- candidatas de temperatura por municipio (estación en el mismo municipio, con las 3 variables)
    cand = []
    for r in st[st["temperatura_min_disponible"].astype(str).str.lower().eq("true") & st["codigo_municipio"].notna()].itertuples():
        w, infos = weekly_station_temperature(int(r.codigo_estacion), daymap)
        if w is None:
            continue
        ok_all = (w[[f"n_dias_{k}" for k in C.TEMP_VARS]] >= C.TEMP_MIN_DAYS).all(axis=1)
        cand.append(dict(codigo_estacion=int(r.codigo_estacion), codigo_municipio=r.codigo_municipio,
                         semanas_ge6_todas=int(ok_all.sum()), cobertura_pct=round(100 * ok_all.mean(), 2), weekly=w,
                         duplicadas=sum(i["fechas_duplicadas"] for i in infos.values())))
    cdf = pd.DataFrame([{k: v for k, v in c.items() if k != "weekly"} for c in cand])
    # ---- estado municipal
    rows, chosen = [], {}
    for m in mun.itertuples():
        mc = cdf[cdf["codigo_municipio"] == m.codigo_municipio] if len(cdf) else cdf
        r = dict(codigo_municipio=m.codigo_municipio, municipio=m.municipio, estaciones_candidatas=";".join(map(str, mc.codigo_estacion)) if len(mc) else "")
        if len(mc) == 0:
            r.update(estado_calidad_temperatura="SIN_ESTACION", codigo_estacion_temperatura=None,
                     detalle="No hay estación del catálogo con temperatura (mín/máx/media) en el mismo municipio.")
        else:
            best = mc.sort_values(["cobertura_pct", "codigo_estacion"], ascending=[False, True]).iloc[0]
            code = int(best.codigo_estacion)
            r.update(codigo_estacion_temperatura=code, cobertura_semanas_verificadas_pct=best.cobertura_pct)
            if code == C.ALDANA_STATION:
                r.update(estado_calidad_temperatura="SERIE_NO_CONFIABLE",
                         detalle=f"Estación 52055230 excluida (mín/máx/media): {ald['dias_min_igual_max']} de {ald['dias_con_3_variables']} días con mín=máx y {ald['dias_media_mayor_max']} con media>máx.")
            elif code == C.CHACHAGUI_STATION:
                r.update(estado_calidad_temperatura="SIN_ESTACION_VALIDADA",
                         detalle="Catálogo IDEAM: 'AEROPUERTO ANTONIO NARIÑO', municipio 'Chachaguí', lat 1,394083, lon -77,290861, 1.796 m. No hay límites municipales ni dato oficial adicional que demuestre que está dentro de Chachagüí: asociación excluida de V2.")
            elif best.cobertura_pct < C.STATION_MIN_WEEK_COVERAGE:
                r.update(estado_calidad_temperatura="ESTACION_COBERTURA_INSUFICIENTE",
                         detalle=f"Cobertura {best.cobertura_pct}% < {C.STATION_MIN_WEEK_COVERAGE}% de semanas verificadas con >=6/7 días en las 3 variables.")
            else:
                r.update(estado_calidad_temperatura="ESTACION_VALIDADA", detalle="Estación del mismo municipio (catálogo) con cobertura suficiente.")
                chosen[m.codigo_municipio] = code
        rows.append(r)
    muni_status = pd.DataFrame(rows)
    # ---- unión a V1
    wk = {c["codigo_estacion"]: c["weekly"] for c in cand}
    v = v1.copy()
    status = muni_status.set_index("codigo_municipio")
    v["estado_calidad_temperatura"] = v["codigo_municipio"].map(status["estado_calidad_temperatura"])
    sc = v["codigo_municipio"].map(status["codigo_estacion_temperatura"])
    show_station = v["estado_calidad_temperatura"].isin(["ESTACION_VALIDADA", "SERIE_NO_CONFIABLE", "ESTACION_COBERTURA_INSUFICIENTE"])
    v["codigo_estacion_temperatura"] = sc.where(show_station).astype("Int64")
    def _m(col):
        return v["codigo_estacion_temperatura"].map(lambda c: meta.loc[c, col] if pd.notna(c) else None)
    v["nombre_estacion_temperatura"] = _m("nombre_estacion")
    v["municipio_estacion_catalogo"] = _m("municipio")
    v["altitud_estacion"] = _m("altitud")
    v["estado_estacion_catalogo"] = _m("estado_catalogo")
    tcols = [f"{k}_semanal" for k in C.TEMP_VARS] + [f"n_dias_{k}" for k in C.TEMP_VARS] + ["n_dias_temperatura"]
    for c in tcols:
        v[c] = np.nan
    valid_mask = v["estado_calidad_temperatura"].eq("ESTACION_VALIDADA")
    allw = pd.concat([w.assign(codigo_estacion_temperatura=c) for c, w in wk.items() if c in set(chosen.values())], ignore_index=True)
    vv = v.loc[valid_mask, ["codigo_estacion_temperatura", "anio", "semana_epidemiologica"]].reset_index().merge(
        allw, on=["codigo_estacion_temperatura", "anio", "semana_epidemiologica"], how="left").set_index("index")
    for c in tcols:
        v.loc[vv.index, c] = vv[c]
    # estado por fila
    ver = v["calendar_verificado"].eq("SI")
    est = v["estado_calidad_temperatura"].copy()
    has_vals = v[[f"{k}_semanal" for k in C.TEMP_VARS]].notna()
    n_ok = has_vals.sum(axis=1)
    row_state = np.where(~ver, "CALENDARIO_NO_VERIFICADO",
                 np.where(n_ok == 3, "VALIDO", np.where(n_ok > 0, "PARCIAL", "INSUFICIENTE_DIAS")))
    v["estado_calidad_temperatura"] = np.where(valid_mask, row_state, est)
    # los días observados solo tienen sentido para filas con estación validada y calendario verificado
    return v, muni_status, cdf.drop(columns=[]), dict(aldana=ald, chachagui=cha, estaciones_elegidas=chosen)


# ----------------------------------------------------------------------------- precipitación (V3)
def build_v3(v1: pd.DataFrame, st: pd.DataFrame, mun: pd.DataFrame, cal: pd.DataFrame):
    daymap = ideam.week_of_date_map(cal)
    meta = _station_meta(st)
    cand, daily_parts, infos_all = [], [], []
    prec_st = st[st["precipitacion_disponible"].astype(str).str.lower().eq("true")]
    for r in prec_st.itertuples():
        s, info = ideam.read_daily(C.PREC_VAR, int(r.codigo_estacion), ideam.PREC_FOLDER)
        if s is None:
            continue
        infos_all.append(dict(codigo_estacion=int(r.codigo_estacion), **info))
        sub = s[(s.index >= "2012-01-01") & (s.index <= "2022-12-31")]
        daily_parts.append(pd.DataFrame({
            "codigo_estacion": int(r.codigo_estacion), "nombre_estacion": r.nombre_estacion,
            "codigo_municipio": r.codigo_municipio, "municipio_catalogo": r.municipio,
            "fecha": sub.index.strftime("%Y-%m-%d"), "valor_original": sub.values,
            "unidad_reportada": PREC_UNIT_REPORTED, "variable_etiqueta": C.PREC_VAR,
            "descripcion_sensor": f"{r.categoria} / {r.tecnologia}", "estado_estacion_catalogo": r.estado_catalogo,
            "estado_validacion_semantica": STATUS_SEM, "fuente_archivo": info["archivo"]}))
        if pd.notna(r.codigo_municipio):
            w = ideam.weekly_stats(s, daymap, "sum").rename(columns={"n_dias": "n_dias_precipitacion_candidata", "valor": "_suma"})
            ok7 = w["n_dias_precipitacion_candidata"] >= C.PREC_MIN_DAYS
            ok6 = w["n_dias_precipitacion_candidata"] >= 6
            cand.append(dict(codigo_estacion=int(r.codigo_estacion), codigo_municipio=r.codigo_municipio,
                             cobertura_7de7_pct=round(100 * ok7.mean(), 2), cobertura_ge6_pct=round(100 * ok6.mean(), 2), weekly=w))
    daily = pd.concat(daily_parts, ignore_index=True)
    cdf = pd.DataFrame([{k: v for k, v in c.items() if k != "weekly"} for c in cand])
    rows, chosen = [], {}
    for m in mun.itertuples():
        mc = cdf[cdf["codigo_municipio"] == m.codigo_municipio] if len(cdf) else cdf
        r = dict(codigo_municipio=m.codigo_municipio, municipio=m.municipio, estaciones_candidatas=";".join(map(str, mc.codigo_estacion)) if len(mc) else "")
        if len(mc) == 0:
            r.update(estado_calidad_precipitacion="SIN_ESTACION", codigo_estacion_precipitacion=None)
        else:
            best = mc.sort_values(["cobertura_7de7_pct", "codigo_estacion"], ascending=[False, True]).iloc[0]
            r.update(codigo_estacion_precipitacion=int(best.codigo_estacion), cobertura_7de7_semanas_verificadas_pct=best.cobertura_7de7_pct,
                     cobertura_ge6_semanas_verificadas_pct=best.cobertura_ge6_pct)
            if best.cobertura_7de7_pct < C.STATION_MIN_WEEK_COVERAGE:
                r["estado_calidad_precipitacion"] = "ESTACION_COBERTURA_INSUFICIENTE"
            else:
                r["estado_calidad_precipitacion"] = "ESTACION_CANDIDATA"
                chosen[m.codigo_municipio] = int(best.codigo_estacion)
        rows.append(r)
    muni_status = pd.DataFrame(rows)
    status = muni_status.set_index("codigo_municipio")
    v = v1.copy()
    v["codigo_estacion_precipitacion"] = v["codigo_municipio"].map(status["codigo_estacion_precipitacion"]).astype("Int64")
    v["nombre_estacion_precipitacion"] = v["codigo_estacion_precipitacion"].map(lambda c: meta.loc[c, "nombre_estacion"] if pd.notna(c) else None)
    v["altitud_estacion_precipitacion"] = v["codigo_estacion_precipitacion"].map(lambda c: meta.loc[c, "altitud"] if pd.notna(c) else None)
    v["estado_estacion_precipitacion_catalogo"] = v["codigo_estacion_precipitacion"].map(lambda c: meta.loc[c, "estado_catalogo"] if pd.notna(c) else None)
    v["n_dias_precipitacion_candidata"] = np.nan
    v["precipitacion_valor_original_suma_semanal"] = np.nan
    v["unidad_reportada_precipitacion"] = PREC_UNIT_REPORTED
    v["estado_validacion_semantica_precipitacion"] = STATUS_SEM
    chosen_codes = set(chosen.values())
    allw = pd.concat([c["weekly"].assign(codigo_estacion_precipitacion=c["codigo_estacion"]) for c in cand if c["codigo_estacion"] in chosen_codes], ignore_index=True)
    mask = v["codigo_municipio"].map(lambda x: x in chosen) & v["calendar_verificado"].eq("SI")
    vv = v.loc[mask, ["codigo_estacion_precipitacion", "anio", "semana_epidemiologica"]].reset_index().merge(
        allw, on=["codigo_estacion_precipitacion", "anio", "semana_epidemiologica"], how="left").set_index("index")
    v.loc[vv.index, "n_dias_precipitacion_candidata"] = vv["n_dias_precipitacion_candidata"]
    cum7 = (v["n_dias_precipitacion_candidata"] >= C.PREC_MIN_DAYS)
    v["cumple_7_de_7_dias"] = cum7.where(v["n_dias_precipitacion_candidata"].notna())
    if PREC_SEMANTICS_CONFIRMED:      # deshabilitado: la semántica sigue pendiente (ver limitaciones_dataset.md)
        sel = vv.index[cum7.loc[vv.index].values]
        v.loc[sel, "precipitacion_valor_original_suma_semanal"] = vv.loc[sel, "_suma"]
    est = np.where(v["codigo_estacion_precipitacion"].isna(), "SIN_ESTACION",
          np.where(v["calendar_verificado"].eq("NO"), "CALENDARIO_NO_VERIFICADO",
          np.where(~v["codigo_municipio"].map(lambda x: x in chosen), "ESTACION_COBERTURA_INSUFICIENTE",
          np.where(v["cumple_7_de_7_dias"].eq(True), "CANDIDATA_7DE7_SEMANTICA_PENDIENTE", "INSUFICIENTE_DIAS"))))
    v["estado_calidad_precipitacion"] = est
    v["habilitado_como_predictor_validado"] = False
    return v, muni_status, daily, pd.DataFrame(infos_all)
