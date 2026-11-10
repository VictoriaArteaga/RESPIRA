"""Procesamiento epidemiológico (SIVIGILA), integración demográfica (DANE) y construcción de V1.

Reglas clave (aprobadas):
 * Ausente != 0: las semanas sin registro quedan NULL con estado AUSENTE; nada se imputa ni se interpola.
 * Un registro con algún componente iracext_1..3 vacío NO se completa: el valor del registro es NULL
   (PARCIAL_VACIOS) y el valor municipal es NULL si algún registro que contribuye está incompleto.
 * Reportes repetidos (misma UPGD + sede + municipio + semana + año): se conservan TODAS las filas y se
   calculan dos interpretaciones alternativas (SUMA, ULTIMO_REPORTE). Ninguna es la oficial.
 * Último reporte = mayor NUM_CON del grupo. Si NUM_CON falta o hay empate en el máximo, el orden no es
   verificable: el resultado es NO_DETERMINABLE (NULL) y se documenta.
"""
from __future__ import annotations
import re, unicodedata
import numpy as np
import pandas as pd
from . import config as C

COUNT_COLS = ["iracext_1", "iracext_2", "iracext_3"]
TOT_COLS = ["totcext_1", "totcext_2", "totcext_3"]


def fold(s) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().strip().lower()


# --------------------------------------------------------------------------------------------- lectura
def load_sivigila() -> pd.DataFrame:
    frames = []
    for y in C.YEARS:
        d = pd.read_csv(C.INTERIM_DIR / f"sivigila_narino_{y}.csv", dtype=str, keep_default_na=False)
        d["anio_archivo"] = y
        d["fuente_archivo"] = f"Datos_{y}_995.xlsx"
        d["fuente_hoja"] = C.SIV_SHEET[y]
        frames.append(d)
    s = pd.concat(frames, ignore_index=True)
    s["excel_row"] = s["excel_row"].astype(int)
    num = ["semana", "ano", "num_con", "ajuste", *COUNT_COLS, *TOT_COLS, "tot_iraext", "tot_exturg"]
    s["_raw_nonnumeric"] = 0
    for c in num:
        raw = s[c].str.strip()
        v = pd.to_numeric(raw.replace("", np.nan), errors="coerce")
        s["_raw_nonnumeric"] += ((raw != "") & v.isna()).astype(int)
        s[c] = v
    s["cod_mun"] = s["cod_mun"].str.strip()
    s["cod_pre_norm"] = s["cod_pre"].str.strip().str.lstrip("0")
    s["cod_sub_norm"] = s["cod_sub"].str.strip().str.lstrip("0")
    return s


def load_population() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (poblacion municipio-año 2012-2022, municipios). Conserva valores originales y dane_libro."""
    fr = []
    for t in ("a", "b"):
        d = pd.read_csv(C.INTERIM_DIR / f"dane_narino_{t}.csv", dtype={"mpio": str})
        fr.append(d)
    p = pd.concat(fr, ignore_index=True)
    p = p[p["area"].astype(str).str.strip().str.lower() == "total"].copy()
    p["anio"] = p["anio"].astype(int)
    p = p[(p["anio"] >= 2012) & (p["anio"] <= 2022)]
    tcols = [f"total_{i}" for i in range(5)]
    p["poblacion_menor_5"] = p[tcols].sum(axis=1, min_count=5)
    hm = [f"hombres_{i}" for i in range(5)] + [f"mujeres_{i}" for i in range(5)]
    p["_suma_hombres_mujeres"] = p[hm].sum(axis=1, min_count=10)
    p = p.rename(columns={"mpio": "codigo_municipio"})
    mun = (p.drop_duplicates("codigo_municipio")[["codigo_municipio", "municipio"]]
           .sort_values("codigo_municipio").reset_index(drop=True))
    mun["departamento"] = "Nariño"
    return p.reset_index(drop=True), mun


# --------------------------------------------------------------------------------------------- normalización
def flag_territory(s: pd.DataFrame, valid_codes: set[str]) -> pd.DataFrame:
    """Banderas territoriales (NO corrige códigos).

    territorio_incongruente  : definición de la auditoría (10 registros): código 52xxx con departamento notificador distinto
                               de Nariño, o código 52000 (no es un municipio).
    departamento_narino_codigo_ajeno : departamento notificador NARIÑO pero código vacío o de otro departamento (hallazgo
                               adicional de esta construcción; no asignable a un municipio de Nariño).
    """
    dep_nar = s["ndep_notif"].map(fold).eq("narino")
    code_nar = s["cod_mun"].str.startswith("52")
    s["territorio_incongruente"] = (code_nar & ~dep_nar) | (s["cod_mun"] == "52000")
    s["departamento_narino_codigo_ajeno"] = dep_nar & ~code_nar
    s["codigo_asignable"] = s["cod_mun"].isin(valid_codes)
    s["motivo_territorial"] = ""
    s.loc[code_nar & ~dep_nar, "motivo_territorial"] = "CODIGO_" + s["cod_mun"] + "_DEPARTAMENTO_NOTIFICADOR_" + s["ndep_notif"].astype(str)
    s.loc[s["cod_mun"] == "52000", "motivo_territorial"] = "CODIGO_52000_NO_ES_MUNICIPIO"
    s.loc[dep_nar & ~code_nar, "motivo_territorial"] = "DEPARTAMENTO_NARINO_CODIGO_" + s["cod_mun"].replace("", "VACIO")
    return s


def prepare_rows(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    s["ira_fila"] = s[COUNT_COLS].sum(axis=1, min_count=3)          # NaN si falta algún componente
    s["tot_fila"] = s[TOT_COLS].sum(axis=1, min_count=3)
    s["fila_ira_completa"] = s[COUNT_COLS].notna().all(axis=1)
    s["fila_tot_completa"] = s[TOT_COLS].notna().all(axis=1)
    s["anio"] = s["anio_archivo"]
    s["anio_discordante"] = s["ano"].notna() & (s["ano"] != s["anio_archivo"])
    s["semana"] = s["semana"].astype("Int64")
    s["grupo_clave"] = (s["anio"].astype(str) + "|" + s["cod_mun"] + "|" + s["semana"].astype(str) + "|"
                        + s["cod_pre_norm"] + "|" + s["cod_sub_norm"])
    s["grupo_n"] = s.groupby("grupo_clave")["excel_row"].transform("size")
    s["es_repetido"] = s["grupo_n"] > 1
    s["grupo_id"] = np.where(
        s["es_repetido"],
        "G" + s["anio"].astype(str) + "-" + s["cod_mun"] + "-S" + s["semana"].astype(str).str.zfill(2)
        + "-P" + s["cod_pre_norm"] + "-" + s["cod_sub_norm"], "")
    return s


def choose_last(s: pd.DataFrame) -> pd.DataFrame:
    """Marca la fila 'último reporte' de cada grupo (mayor NUM_CON) y su estado de determinabilidad."""
    s = s.copy()
    s["es_ultimo"] = False
    s["ultimo_determinable"] = True
    s["orden_coincide_con_fila_excel"] = pd.NA
    single = ~s["es_repetido"]
    s.loc[single, "es_ultimo"] = True
    rep = s[s["es_repetido"]]
    for key, g in rep.groupby("grupo_clave", sort=False):
        nc = g["num_con"]
        if nc.isna().any() or (nc == nc.max()).sum() != 1:
            s.loc[g.index, "ultimo_determinable"] = False
            continue
        i = nc.idxmax()
        s.loc[i, "es_ultimo"] = True
        s.loc[g.index, "orden_coincide_con_fila_excel"] = bool(g["excel_row"].idxmax() == i)
    return s


# --------------------------------------------------------------------------------------------- agregación
def aggregate_mw(s: pd.DataFrame) -> pd.DataFrame:
    """Agrega a municipio-semana (solo filas asignables a un municipio de la cuadrícula)."""
    a = s[s["codigo_asignable"]].copy()
    K = ["cod_mun", "anio", "semana"]
    g = a.groupby(K, sort=False)
    base = pd.DataFrame({
        "numero_reportes": g.size(),
        "numero_grupos_reporte": g["grupo_clave"].nunique(),
        "n_filas_ira_con_vacios": g["fila_ira_completa"].apply(lambda x: int((~x).sum())),
        "n_filas_tot_con_vacios": g["fila_tot_completa"].apply(lambda x: int((~x).sum())),
        "n_registros_territorio_incongruente": g["territorio_incongruente"].sum().astype(int),
        "n_registros_con_ajuste": g["ajuste"].apply(lambda x: int((x.fillna(0) > 0).sum())),
        "ira_suma_parcial_disponible": g["ira_fila"].sum(min_count=1),
        "tot_suma_parcial_disponible": g["tot_fila"].sum(min_count=1),
        "identificador_origen": g["excel_row"].apply(lambda x: ";".join(f"r{int(v)}" for v in sorted(x))),
        "fuente_archivo": g["fuente_archivo"].first(),
        "fuente_hoja": g["fuente_hoja"].first(),
    })
    rep = a[a["es_repetido"]]
    gr = rep.groupby(K, sort=False)
    base["numero_grupos_repetidos"] = gr["grupo_clave"].nunique().reindex(base.index).fillna(0).astype(int)
    base["ids_grupos_repetidos"] = gr["grupo_id"].apply(lambda x: ";".join(sorted(set(x)))).reindex(base.index).fillna("")
    base["n_filas_en_grupos_repetidos"] = gr.size().reindex(base.index).fillna(0).astype(int)
    # ---- ULTIMO_REPORTE: filas elegidas; grupos no determinables
    nd = a[~a["ultimo_determinable"]].groupby(K)["grupo_clave"].nunique()
    base["n_grupos_orden_no_determinable"] = nd.reindex(base.index).fillna(0).astype(int)
    sel = a[a["es_ultimo"]]
    gs = sel.groupby(K, sort=False)
    base["n_sel_ira_con_vacios"] = gs["fila_ira_completa"].apply(lambda x: int((~x).sum())).reindex(base.index).fillna(0).astype(int)
    base["n_sel_tot_con_vacios"] = gs["fila_tot_completa"].apply(lambda x: int((~x).sum())).reindex(base.index).fillna(0).astype(int)
    base["ira_ultimo_parcial"] = gs["ira_fila"].sum(min_count=1).reindex(base.index)
    base["tot_ultimo_parcial"] = gs["tot_fila"].sum(min_count=1).reindex(base.index)
    # ---- valores finales (NULL si no hay evidencia completa)
    suma_ok = base["n_filas_ira_con_vacios"] == 0
    base["iracext_0_4_notificado_suma"] = base["ira_suma_parcial_disponible"].where(suma_ok)
    ult_ok = (base["n_sel_ira_con_vacios"] == 0) & (base["n_grupos_orden_no_determinable"] == 0)
    base["iracext_0_4_notificado_ultimo_reporte"] = base["ira_ultimo_parcial"].where(ult_ok)
    base["totcext_0_4_experimental_suma"] = base["tot_suma_parcial_disponible"].where(base["n_filas_tot_con_vacios"] == 0)
    tot_ok = (base["n_sel_tot_con_vacios"] == 0) & (base["n_grupos_orden_no_determinable"] == 0)
    base["totcext_0_4_experimental_ultimo_reporte"] = base["tot_ultimo_parcial"].where(tot_ok)
    base["estado_dato_ira"] = np.where(suma_ok, "COMPLETO", "PARCIAL_VACIOS")
    est_u = np.where(base["n_grupos_orden_no_determinable"] > 0, "NO_DETERMINABLE",
                     np.where(base["n_sel_ira_con_vacios"] > 0, "PARCIAL_VACIOS", "COMPLETO"))
    base["estado_dato_ira_ultimo_reporte"] = est_u
    base["tiene_reportes_repetidos"] = base["numero_grupos_repetidos"] > 0
    base["estado_orden_ultimo_reporte"] = np.where(~base["tiene_reportes_repetidos"], "NO_APLICA",
                                                   np.where(base["n_grupos_orden_no_determinable"] > 0, "NO_DETERMINABLE", "DETERMINADO"))
    for src, dst in (("iracext_0_4_notificado_suma", "proporcion_ira_sobre_consultas_experimental_suma"),
                     ("iracext_0_4_notificado_ultimo_reporte", "proporcion_ira_sobre_consultas_experimental_ultimo_reporte")):
        tcol = "totcext_0_4_experimental_suma" if src.endswith("suma") else "totcext_0_4_experimental_ultimo_reporte"
        base[dst] = (base[src] / base[tcol].where(base[tcol] > 0))
    return base.reset_index().rename(columns={"cod_mun": "codigo_municipio", "semana": "semana_epidemiologica"})


# --------------------------------------------------------------------------------------------- V1
def build_v1(agg: pd.DataFrame, pop: pd.DataFrame, mun: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    grid = pd.MultiIndex.from_product(
        [mun["codigo_municipio"], [(y, w) for y in C.YEARS for w in range(1, C.WEEKS_IN_YEAR[y] + 1)]]
    ).to_frame(index=False)
    grid["anio"] = grid[1].map(lambda t: t[0])
    grid["semana_epidemiologica"] = grid[1].map(lambda t: t[1])
    grid = grid.rename(columns={0: "codigo_municipio"}).drop(columns=1)
    v = grid.merge(mun, on="codigo_municipio", how="left")
    v["regimen"] = v["anio"].map(C.regimen)
    v["completitud_no_verificada"] = v["anio"].eq(2021)
    v = v.merge(cal[["anio", "semana_epidemiologica", "semana_inicio", "semana_fin"]], on=["anio", "semana_epidemiologica"], how="left")
    v["calendar_verificado"] = np.where(v["anio"].isin(C.CALENDAR_VERIFIED), "SI", "NO")
    v["calendar_version"] = C.CALENDAR_VERSION
    v = v.merge(agg, on=["codigo_municipio", "anio", "semana_epidemiologica"], how="left")
    v["semana_ausente"] = v["numero_reportes"].isna()
    v["estado_dato_ira"] = v["estado_dato_ira"].fillna("AUSENTE")
    v["estado_dato_ira_ultimo_reporte"] = v["estado_dato_ira_ultimo_reporte"].fillna("AUSENTE")
    v["estado_orden_ultimo_reporte"] = v["estado_orden_ultimo_reporte"].fillna("AUSENTE")
    v["numero_reportes"] = v["numero_reportes"].fillna(0).astype(int)      # 0 reportes = conteo de FILAS (no el indicador)
    v["tiene_reportes_repetidos"] = v["tiene_reportes_repetidos"].fillna(False).astype(bool)
    for c in ("numero_grupos_reporte", "numero_grupos_repetidos", "n_filas_en_grupos_repetidos",
              "n_registros_territorio_incongruente", "n_registros_con_ajuste"):
        v[c] = v[c].fillna(0).astype(int)
    v["ids_grupos_repetidos"] = v["ids_grupos_repetidos"].fillna("")
    v["identificador_origen"] = v["identificador_origen"].fillna("")
    v["tiene_codigo_territorial_incongruente"] = v["n_registros_territorio_incongruente"] > 0
    # población (valores originales; sin reescalar el salto 2017->2018)
    pp = pop[["codigo_municipio", "anio", "poblacion_menor_5", "dane_libro", "excel_row"]].rename(columns={"excel_row": "poblacion_fila_origen"})
    v = v.merge(pp, on=["codigo_municipio", "anio"], how="left")
    # fuente SIVIGILA también para filas ausentes (el archivo/hoja esperados del año)
    v["fuente_archivo"] = v["fuente_archivo"].fillna(v["anio"].map(lambda y: f"Datos_{y}_995.xlsx"))
    v["fuente_hoja"] = v["fuente_hoja"].fillna(v["anio"].map(C.SIV_SHEET))
    # calidad
    obs, code = [], []
    for r in v.itertuples(index=False):
        o = []
        if r.estado_dato_ira == "AUSENTE":
            o.append("SEMANA_AUSENTE_SIN_REGISTRO_NO_ES_CERO")
        if r.estado_dato_ira == "PARCIAL_VACIOS":
            o.append(f"PARCIAL_VACIOS:{r.n_filas_ira_con_vacios}_registros_con_componente_vacio")
        if r.tiene_reportes_repetidos:
            o.append(f"REPORTES_REPETIDOS:{r.numero_grupos_repetidos}_grupo(s)")
        if r.estado_orden_ultimo_reporte == "NO_DETERMINABLE":
            o.append("ULTIMO_REPORTE_NO_DETERMINABLE")
        if r.tiene_codigo_territorial_incongruente:
            o.append(f"CODIGO_TERRITORIAL_INCONGRUENTE:{r.n_registros_territorio_incongruente}_registro(s)")
        if r.n_registros_con_ajuste > 0:
            o.append(f"AJUSTE_REPORTADO:{r.n_registros_con_ajuste}")
        if r.completitud_no_verificada:
            o.append("COMPLETITUD_2021_NO_VERIFICADA")
        if r.calendar_verificado == "NO":
            o.append("CALENDARIO_NO_VERIFICADO")
        if pd.isna(r.poblacion_menor_5):
            o.append("POBLACION_AUSENTE")
        obs.append(";".join(o))
        if r.estado_dato_ira == "AUSENTE":
            code.append("Q3_AUSENTE")
        elif r.estado_dato_ira == "PARCIAL_VACIOS":
            code.append("Q2_PARCIAL_VACIOS")
        elif r.tiene_reportes_repetidos or r.tiene_codigo_territorial_incongruente or r.n_registros_con_ajuste > 0:
            code.append("Q1_COMPLETO_CON_ALERTAS")
        else:
            code.append("Q0_COMPLETO")
    v["observaciones_calidad"] = obs
    v["codigo_calidad"] = code
    return v
