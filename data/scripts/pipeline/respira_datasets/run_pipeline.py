"""Orquestación: construye V1, V2, V3, tablas supervisadas, validaciones y metadatos.

Uso (desde data/pipeline):   python -m respira_datasets.run_pipeline [--skip-extract]
Idempotente: reescribe los mismos archivos en data/processed/{v1,v2,v3,supervised,metadata}; no toca originales.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from . import config as C, build_v1 as B, build_climate as CL, ideam, supervised as S, validate as V, stage1_extract

OUT = C.OUT_DIR
D = {  # diccionario de columnas (descripción) compartido por V1/V2/V3
 "codigo_municipio": "Código DIVIPOLA de 5 dígitos (texto), tal como figura en SIVIGILA/DANE; no se corrige.",
 "municipio": "Nombre del municipio según DANE.", "departamento": "Departamento (Nariño).",
 "anio": "Año epidemiológico reportado por SIVIGILA (coincide con el año del libro).",
 "semana_epidemiologica": "Semana epidemiológica reportada por SIVIGILA (53 solo en 2014 y 2020).",
 "regimen": "PRE_PANDEMIA (<=2019), PANDEMIA (2020-2021), POST_PANDEMIA (2022).",
 "calendar_verificado": "SI solo para 2016 y 2022 (boletines INS SE52); NO para los demás años.",
 "calendar_version": "Versión de la tabla de calendario.", "semana_inicio": "Inicio (domingo) de la semana; NULL si el calendario no está verificado.",
 "semana_fin": "Fin (sábado) de la semana; NULL si el calendario no está verificado.",
 "iracext_0_4_notificado_suma": "iracext_1+iracext_2+iracext_3 sumado sobre TODOS los registros del municipio-semana (interpretación SUMA). Conteo notificado; NO es incidencia ni pacientes únicos. NULL si ausente o con vacíos.",
 "iracext_0_4_notificado_ultimo_reporte": "Igual, pero en cada grupo repetido solo el registro de mayor NUM_CON (interpretación ULTIMO_REPORTE). NULL si ausente, con vacíos u orden no determinable. Ninguna interpretación es la oficial.",
 "numero_reportes": "Número de registros (filas) SIVIGILA del municipio-semana. 0 = sin registros (AUSENTE); no es el indicador.",
 "numero_grupos_reporte": "Grupos distintos UPGD+sede dentro del municipio-semana.",
 "tiene_reportes_repetidos": "TRUE si algún grupo UPGD+sede tiene más de un registro en la misma semana.",
 "numero_grupos_repetidos": "Cantidad de grupos con repetición.", "ids_grupos_repetidos": "Identificadores de los grupos repetidos (detalle en v1/reportes_repetidos_detalle.csv).",
 "n_filas_en_grupos_repetidos": "Registros que pertenecen a grupos repetidos.",
 "n_grupos_orden_no_determinable": "Grupos repetidos sin NUM_CON único máximo (último reporte no verificable).",
 "estado_orden_ultimo_reporte": "NO_APLICA / DETERMINADO / NO_DETERMINABLE / AUSENTE. Criterio: mayor NUM_CON; empate o NUM_CON nulo => NO_DETERMINABLE.",
 "estado_dato_ira": "Estado del dato bajo SUMA: COMPLETO / PARCIAL_VACIOS / AUSENTE.",
 "estado_dato_ira_ultimo_reporte": "Estado bajo ULTIMO_REPORTE: COMPLETO / PARCIAL_VACIOS / NO_DETERMINABLE / AUSENTE.",
 "completitud_no_verificada": "TRUE para 2021 (conteo oficial INS pendiente).",
 "totcext_0_4_experimental_suma": "EXPERIMENTAL: totcext_1+2+3 (SUMA). Significado pendiente de confirmación del INS.",
 "totcext_0_4_experimental_ultimo_reporte": "EXPERIMENTAL: totcext_1+2+3 (ULTIMO_REPORTE).",
 "proporcion_ira_sobre_consultas_experimental_suma": "EXPERIMENTAL: ira/totcext (SUMA); NULL si denominador nulo o cero. No es tasa ni incidencia.",
 "proporcion_ira_sobre_consultas_experimental_ultimo_reporte": "EXPERIMENTAL: ira/totcext (ULTIMO_REPORTE).",
 "n_registros_territorio_incongruente": "Registros del municipio-semana con código/departamento incongruente (no corregidos).",
 "tiene_codigo_territorial_incongruente": "TRUE si n_registros_territorio_incongruente>0.",
 "n_registros_con_ajuste": "Registros con campo ajuste > 0.",
 "poblacion_menor_5": "Población DANE 0-4 años (suma Total_0..4, área Total), valor original sin reescalar.",
 "dane_libro": "Libro DANE de origen (DANE_2005_2017 / DANE_2018_2042). Hay un salto de serie 2017->2018 sin ajustar.",
 "poblacion_fila_origen": "Fila Excel del libro DANE.",
 "codigo_calidad": "Q0_COMPLETO / Q1_COMPLETO_CON_ALERTAS / Q2_PARCIAL_VACIOS / Q3_AUSENTE (según SUMA).",
 "observaciones_calidad": "Lista de alertas separadas por ';'.",
 "fuente_archivo": "Libro SIVIGILA de origen.", "fuente_hoja": "Hoja del libro usada.",
 "identificador_origen": "Filas Excel (rN) de los registros originales que dan origen al resultado.",
 "semana_ausente": "TRUE si no hay registros SIVIGILA.", "estado_calidad_temperatura": "VALIDO / PARCIAL / INSUFICIENTE_DIAS / CALENDARIO_NO_VERIFICADO / SIN_ESTACION / SIN_ESTACION_VALIDADA / SERIE_NO_CONFIABLE / ESTACION_COBERTURA_INSUFICIENTE.",
 "temperatura_min_semanal": "°C. Mínimo de TSSM_MN_D en la semana (>=6/7 días válidos).", "temperatura_max_semanal": "°C. Máximo de TSSM_MX_D (>=6/7 días).",
 "temperatura_media_semanal": "°C. Media aritmética de TSSM_MEDIA_D (>=6/7 días).",
 "n_dias_temperatura_min": "Días válidos de la variable.", "n_dias_temperatura_max": "Días válidos de la variable.", "n_dias_temperatura_media": "Días válidos de la variable.",
 "n_dias_temperatura": "Mínimo de los días válidos entre las 3 variables.",
 "codigo_estacion_temperatura": "Estación IDEAM del mismo municipio (catálogo).", "nombre_estacion_temperatura": "Nombre en el catálogo.",
 "municipio_estacion_catalogo": "Municipio según catálogo IDEAM.", "altitud_estacion": "m s. n. m. (catálogo).", "estado_estacion_catalogo": "Estado en el catálogo.",
 "codigo_estacion_precipitacion": "Estación candidata del mismo municipio.", "nombre_estacion_precipitacion": "Nombre en el catálogo.",
 "altitud_estacion_precipitacion": "Altitud (catálogo).", "estado_estacion_precipitacion_catalogo": "Estado en el catálogo.",
 "n_dias_precipitacion_candidata": "Días con valor original PTPM_CON_INTER en la semana (solo calendario verificado).",
 "precipitacion_valor_original_suma_semanal": "Suma de valores originales. NULL: la acumulación no está justificada mientras IDEAM no confirme semántica/unidad.",
 "unidad_reportada_precipitacion": "Unidad reportada en los metadatos locales; no confirmada.",
 "estado_validacion_semantica_precipitacion": "SEMANTICA_PENDIENTE_CONFIRMACION.", "cumple_7_de_7_dias": "TRUE si la semana tiene 7/7 días con valor.",
 "estado_calidad_precipitacion": "CANDIDATA_7DE7_SEMANTICA_PENDIENTE / INSUFICIENTE_DIAS / CALENDARIO_NO_VERIFICADO / SIN_ESTACION / ESTACION_COBERTURA_INSUFICIENTE.",
 "habilitado_como_predictor_validado": "Siempre FALSE: no usar como característica climática confirmada.",
}
V1_COLS = ["codigo_municipio", "municipio", "departamento", "anio", "semana_epidemiologica", "regimen", "calendar_verificado", "calendar_version",
 "semana_inicio", "semana_fin", "iracext_0_4_notificado_suma", "iracext_0_4_notificado_ultimo_reporte", "numero_reportes", "numero_grupos_reporte",
 "tiene_reportes_repetidos", "numero_grupos_repetidos", "ids_grupos_repetidos", "n_filas_en_grupos_repetidos", "n_grupos_orden_no_determinable",
 "estado_orden_ultimo_reporte", "estado_dato_ira", "estado_dato_ira_ultimo_reporte", "completitud_no_verificada",
 "totcext_0_4_experimental_suma", "totcext_0_4_experimental_ultimo_reporte", "proporcion_ira_sobre_consultas_experimental_suma",
 "proporcion_ira_sobre_consultas_experimental_ultimo_reporte", "n_registros_territorio_incongruente", "tiene_codigo_territorial_incongruente",
 "n_registros_con_ajuste", "poblacion_menor_5", "dane_libro", "poblacion_fila_origen", "semana_ausente", "codigo_calidad", "fuente_archivo", "fuente_hoja",
 "identificador_origen", "observaciones_calidad"]
V2_EXTRA = ["temperatura_min_semanal", "temperatura_max_semanal", "temperatura_media_semanal", "n_dias_temperatura", "n_dias_temperatura_min",
 "n_dias_temperatura_max", "n_dias_temperatura_media", "codigo_estacion_temperatura", "nombre_estacion_temperatura", "municipio_estacion_catalogo",
 "altitud_estacion", "estado_estacion_catalogo", "estado_calidad_temperatura"]
V3_EXTRA = ["codigo_estacion_precipitacion", "nombre_estacion_precipitacion", "altitud_estacion_precipitacion", "estado_estacion_precipitacion_catalogo",
 "n_dias_precipitacion_candidata", "cumple_7_de_7_dias", "precipitacion_valor_original_suma_semanal", "unidad_reportada_precipitacion",
 "estado_validacion_semantica_precipitacion", "estado_calidad_precipitacion", "habilitado_como_predictor_validado"]


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write(df: pd.DataFrame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n", float_format="%.10g")   # NULL -> campo vacío
    return path


def dict_df(df: pd.DataFrame, extra: dict | None = None) -> pd.DataFrame:
    dd = {**D, **(extra or {})}
    return pd.DataFrame([dict(columna=c, tipo=str(df[c].dtype), descripcion=dd.get(c, "Ver metadata/reglas_transformacion.md")) for c in df.columns])


def coverage_v1(v1: pd.DataFrame) -> pd.DataFrame:
    g = v1.groupby(["codigo_municipio", "municipio", "anio"])
    return g.agg(semanas_malla=("semana_epidemiologica", "size"),
                 completas=("estado_dato_ira", lambda s: int((s == "COMPLETO").sum())),
                 parciales_vacios=("estado_dato_ira", lambda s: int((s == "PARCIAL_VACIOS").sum())),
                 ausentes=("estado_dato_ira", lambda s: int((s == "AUSENTE").sum())),
                 ultimo_no_determinable=("estado_dato_ira_ultimo_reporte", lambda s: int((s == "NO_DETERMINABLE").sum())),
                 semanas_con_repetidos=("tiene_reportes_repetidos", "sum"),
                 registros_territorio_incongruente=("n_registros_territorio_incongruente", "sum"),
                 poblacion_menor_5=("poblacion_menor_5", "first"), dane_libro=("dane_libro", "first"),
                 regimen=("regimen", "first"), calendar_verificado=("calendar_verificado", "first")).reset_index()


def git_info() -> dict:
    def g(*a):
        try:
            return subprocess.run(["git", *a], cwd=C.REPO_ROOT, capture_output=True, text=True).stdout.strip()
        except Exception:
            return ""
    return dict(branch=g("rev-parse", "--abbrev-ref", "HEAD"), commit=g("rev-parse", "HEAD"), working_tree_dirty=bool(g("status", "--porcelain")))


def main(skip_extract: bool = False):
    t0 = datetime.now(timezone.utc)
    if not skip_extract:
        stage1_extract.run()
    log = []
    siv = B.load_sivigila(); pop, mun = B.load_population()
    siv = B.choose_last(B.prepare_rows(B.flag_territory(siv, set(mun.codigo_municipio))))
    cal = ideam.verified_calendar()
    agg = B.aggregate_mw(siv)
    v1_full = B.build_v1(agg, pop, mun, cal)
    v1 = v1_full[V1_COLS]
    log.append(f"V1 construido: {v1.shape}")

    st = ideam.load_stations(mun)
    v2_full, mstat2, cdf2, evid = CL.build_v2(v1_full, st, mun, cal)
    v2 = v2_full[V1_COLS + V2_EXTRA]
    v2_valida = v2[v2.estado_calidad_temperatura == "VALIDO"]
    v3_full, mstat3, daily, ideam_info = CL.build_v3(v1_full, st, mun, cal)
    v3 = v3_full[V1_COLS + V3_EXTRA]
    log.append(f"V2: {v2.shape}, temperatura VALIDA {len(v2_valida)}; V3: {v3.shape}")

    # ---------------- salidas V1/V2/V3
    write(v1, OUT / "v1/RESPIRA_V1.csv")
    write(dict_df(v1), OUT / "v1/diccionario_V1.csv")
    write(coverage_v1(v1), OUT / "v1/cobertura_V1.csv")
    rep = siv[siv.es_repetido].sort_values(["grupo_id", "excel_row"])
    write(rep[["grupo_id", "anio", "cod_mun", "semana", "cod_pre", "cod_sub", "excel_row", "fuente_archivo", "fuente_hoja", "num_con", "fec_not", "ajuste",
               "iracext_1", "iracext_2", "iracext_3", "ira_fila", "totcext_1", "totcext_2", "totcext_3", "es_ultimo", "ultimo_determinable",
               "orden_coincide_con_fila_excel"]].assign(criterio_orden="NUM_CON_MAXIMO_UNICO"),
          OUT / "v1/reportes_repetidos_detalle.csv")
    rech = siv[~siv.codigo_asignable | siv.territorio_incongruente | siv.departamento_narino_codigo_ajeno]
    write(rech[["anio", "excel_row", "fuente_archivo", "fuente_hoja", "cod_mun", "ndep_notif", "nmun_notif", "semana", "cod_pre", "num_con", "iracext_1", "iracext_2", "iracext_3",
                "territorio_incongruente", "departamento_narino_codigo_ajeno", "codigo_asignable", "motivo_territorial"]].assign(
        tratamiento=np.where(rech.codigo_asignable, "INCLUIDO_EN_MUNICIPIO_POR_CODIGO_ORIGINAL_CON_BANDERA", "EXCLUIDO_DE_LA_CUADRICULA_NO_ASIGNABLE_CONSERVADO_AQUI")),
          OUT / "v1/registros_territoriales_marcados.csv")

    write(v2, OUT / "v2/RESPIRA_V2.csv")
    write(v2_valida, OUT / "v2/RESPIRA_V2_solo_temperatura_valida.csv")
    write(dict_df(v2), OUT / "v2/diccionario_V2.csv")
    def _c2(g):
        ok = g.estado_calidad_temperatura == "VALIDO"
        d = dict(semanas_temperatura_valida=int(ok.sum()), semanas_ira_completa_y_temperatura_valida=int((ok & (g.estado_dato_ira == "COMPLETO")).sum()))
        for y in C.CALENDAR_VERIFIED:
            d[f"semanas_temperatura_valida_{y}"] = int((ok & (g.anio == y)).sum())
        return pd.Series(d)
    cov2 = mstat2.merge(v2_full.groupby("codigo_municipio")[["estado_calidad_temperatura", "estado_dato_ira", "anio"]].apply(_c2).reset_index(),
                        on="codigo_municipio", how="left")
    write(cov2, OUT / "v2/cobertura_V2.csv")
    write(cdf2.sort_values(["codigo_municipio", "codigo_estacion"]), OUT / "v2/estaciones_temperatura_evaluadas.csv")

    write(v3, OUT / "v3/RESPIRA_V3_CANDIDATA_SEMANTICA_PENDIENTE.csv")
    write(dict_df(v3), OUT / "v3/diccionario_V3.csv")
    def _c3(g):
        ok = g.estado_calidad_precipitacion == "CANDIDATA_7DE7_SEMANTICA_PENDIENTE"
        return pd.Series(dict(semanas_candidatas_7de7=int(ok.sum()), semanas_ira_completa_y_candidata_7de7=int((ok & (g.estado_dato_ira == "COMPLETO")).sum())))
    cov3 = mstat3.merge(v3_full.groupby("codigo_municipio")[["estado_calidad_precipitacion", "estado_dato_ira"]].apply(_c3).reset_index(),
                        on="codigo_municipio", how="left")
    write(cov3, OUT / "v3/cobertura_V3.csv")
    write(daily, OUT / "v3/precipitacion_diaria_candidata_preparacion.csv")

    # ---------------- supervisadas (V1 y V2; V3 no tiene variable validada)
    sup = {}
    for variant in S.VARIANTS:
        for h in C.HORIZONS:
            sup[f"V1_{variant}_h{h}"] = S.build(v1_full, variant, h)
    validados = set(mstat2.loc[mstat2.estado_calidad_temperatura == "ESTACION_VALIDADA", "codigo_municipio"])
    v2s = v2_full[v2_full.codigo_municipio.isin(validados)]
    for variant in S.VARIANTS:
        for h in C.HORIZONS:
            sup[f"V2_{variant}_h{h}"] = S.build(v2s, variant, h, temp=True)
    for k, t in sup.items():
        write(t, OUT / f"supervised/supervisada_{k}.csv")
    # diccionario supervisado
    sd = [("codigo_municipio", "Llave"), ("municipio", "Nombre"), ("anio", "Año epidemiológico de t"), ("semana_epidemiologica", "Semana de t"),
          ("posicion_secuencial", "Posición 0..573 en la malla; usada para desplazar"), ("interpretacion_reportes", "SUMA o ULTIMO_REPORTE (escenario alternativo)"),
          ("horizonte_semanas", "2 o 3"), ("ira_t", "Indicador en t"), ("ira_lag1..ira_lag4", "Indicador en t-1..t-4 (NULL si fuente ausente/parcial o si cruza transición de año no validada)"),
          ("target_ira_t_plus_2 / target_ira_t_plus_3", "Indicador en t+h (solo futuro)"), ("anio_objetivo/semana_objetivo", "Semana objetivo"),
          ("motivo_rezagos_nulos / motivo_target_nulo", "FUERA_DE_RANGO, TRANSICION_ANIO_NO_VALIDADA, FUENTE_AUSENTE, FUENTE_PARCIAL_VACIOS, FUENTE_NO_DETERMINABLE"),
          ("fila_completa_ira", "t, lags 1-4 y objetivo no nulos"), ("habilitado_entrenamiento", "Siempre FALSE en esta etapa"), ("motivo_no_habilitado", "Pendientes que lo impiden"),
          ("temperatura_*_semanal_t, temperatura_media_lagK, temperatura_disponible_t", "Solo en tablas V2: temperatura de t y media en t-1..t-4 (solo años con calendario verificado)")]
    write(pd.DataFrame(sd, columns=["columna", "descripcion"]), OUT / "supervised/diccionario_supervisadas.csv")

    # ---------------- control contra el piloto (312 filas)
    pil = pd.read_csv(C.REPO_ROOT / "data/processed/pilot/piloto_respira_2016_2022.csv", encoding="utf-8-sig")
    pil["codigo_municipio"] = pil.municipality_divipola.astype(str).str.zfill(5)
    m = pil.merge(v2_full, left_on=["codigo_municipio", "year", "epi_week"], right_on=["codigo_municipio", "anio", "semana_epidemiologica"], how="left")
    ira_ok = ((m.ira_under5_reported_consultations == m.iracext_0_4_notificado_suma) | (m.ira_under5_reported_consultations.isna() & m.iracext_0_4_notificado_suma.isna()))
    p_diff = m[~ira_ok][["codigo_municipio", "year", "epi_week", "ira_under5_reported_consultations", "iracext_0_4_notificado_suma", "estado_dato_ira"]]
    # temperatura: Funes y Samaniego (Chachagüí excluido en V2)
    mt = m[m.codigo_municipio.isin(["52287", "52678"])]
    tcmp = {}
    for a, b in (("temp_min_weekly", "temperatura_min_semanal"), ("temp_max_weekly", "temperatura_max_semanal"), ("temp_mean_weekly", "temperatura_media_semanal")):
        tcmp[b] = int((~(np.isclose(mt[a], mt[b], equal_nan=True))).sum())
    pilot_check = V._r("18_control_contra_piloto_312_filas", "PASS" if len(p_diff) == 0 and sum(tcmp.values()) == 0 else "WARN", len(p_diff) + sum(tcmp.values()), "MEDIA",
                       f"IRA (SUMA) vs piloto en {len(pil)} filas: {len(p_diff)} diferencias {p_diff.values.tolist()[:6]}. Temperatura Funes+Samaniego ({len(mt)} filas) diferencias por variable: {tcmp}. Chachagüí no se compara (excluido de V2).",
                       "Informativo; el piloto no se modifica")
    ctx = dict(v1=v1, v2=v2, v3=v3, v2_valida=v2_valida, rows=siv, pop=pop, supervised=sup, evid=evid, pilot_check=pilot_check)
    val = V.run_all(ctx)
    write(val, OUT / "metadata/validaciones.csv")

    # ---------------- resumen de calidad
    rc = []
    for name, d in (("V1", v1), ("V2", v2), ("V3", v3)):
        rc.append(dict(dataset=name, filas=len(d), columnas=d.shape[1], municipios=d.codigo_municipio.nunique(), anios="2012-2022",
                       semanas_completas=int((d.estado_dato_ira == "COMPLETO").sum()), semanas_parciales=int((d.estado_dato_ira == "PARCIAL_VACIOS").sum()),
                       semanas_ausentes=int((d.estado_dato_ira == "AUSENTE").sum()), poblacion_presente=int(d.poblacion_menor_5.notna().sum()),
                       temperatura_valida=int((d.get("estado_calidad_temperatura", pd.Series(dtype=str)) == "VALIDO").sum()) if name == "V2" else "",
                       precipitacion_candidata_7de7=int((d.get("estado_calidad_precipitacion", pd.Series(dtype=str)) == "CANDIDATA_7DE7_SEMANTICA_PENDIENTE").sum()) if name == "V3" else "",
                       estado_construccion="CONSTRUIDO", calidad_suficiente="SOLO_V1_PARA_USO_DESCRIPTIVO" if name == "V1" else ("PARCIAL_2016_2022" if name == "V2" else "NO"),
                       habilitado_entrenamiento="NO"))
    for k, t in sup.items():
        rc.append(dict(dataset=f"supervisada_{k}", filas=len(t), columnas=t.shape[1], municipios=t.codigo_municipio.nunique(), anios="2012-2022",
                       semanas_completas=int(t.fila_completa_ira.sum()), estado_construccion="CANDIDATA", calidad_suficiente="NO", habilitado_entrenamiento="NO"))
    write(pd.DataFrame(rc), OUT / "metadata/resumen_calidad.csv")

    # ---------------- fuentes y hashes
    fu = []
    for y in C.YEARS:
        p = C.SOURCE_DIR / "SIVIGILA" / f"Datos_{y}_995.xlsx"; fu.append(("SIVIGILA", p.name, C.SIV_SHEET[y], p.stat().st_size, sha(p)))
    for t in ("a", "b"):
        p = C.SOURCE_DIR / __import__("respira_datasets.dane", fromlist=["x"]).DANE_BOOKS[t][0]; fu.append(("DANE", p.name, "", p.stat().st_size, sha(p)))
    for r in st.itertuples():
        for var, folder in [*[(v, ideam.TEMP_FOLDER) for v in C.TEMP_VARS.values()], (C.PREC_VAR, ideam.PREC_FOLDER)]:
            p = C.SOURCE_DIR / folder / f"{var}@{int(r.codigo_estacion)}.data"
            if p.exists():
                fu.append(("IDEAM", p.name, "", p.stat().st_size, sha(p)))
    p = C.REF_DIR / "estaciones_candidatas_ideam.csv"; fu.append(("REFERENCIA_REPO", "reports/estaciones_candidatas_ideam.csv", "", p.stat().st_size, sha(p)))
    p = C.REF_DIR / "metadatos_variables_ideam.csv"; fu.append(("REFERENCIA_REPO", "reports/metadatos_variables_ideam.csv", "", p.stat().st_size, sha(p)))
    write(pd.DataFrame(fu, columns=["fuente", "archivo", "hoja", "bytes", "sha256"]), OUT / "metadata/fuentes_utilizadas.csv")

    # documentos (texto)
    from . import docs
    docs.write_all(OUT / "metadata", dict(v1=v1, v2=v2, v3=v3, v2_valida=v2_valida, val=val, cov2=cov2, cov3=cov3, sup=sup, evid=evid, siv=siv,
                                           mstat2=mstat2, mstat3=mstat3, log=log))

    # manifest
    outs = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name not in ("manifest.json",) and "pilot" not in p.parts)
    code = sorted((C.REPO_ROOT / "data/scripts/pipeline/respira_datasets").glob("*.py"))
    man = dict(construido_utc=t0.isoformat(timespec="seconds"), pipeline_version=C.PIPELINE_VERSION, calendar_version=C.CALENDAR_VERSION,
               python=sys.version.split()[0], pandas=pd.__version__, git=git_info(), fuentes_dir=str(C.SOURCE_DIR),
               parametros=dict(temp_min_dias=C.TEMP_MIN_DAYS, prec_min_dias=C.PREC_MIN_DAYS, cobertura_estacion_pct=C.STATION_MIN_WEEK_COVERAGE,
                               calendario_verificado=list(C.CALENDAR_VERIFIED), lags=C.LAGS, horizontes=C.HORIZONS, prec_semantica_confirmada=CL.PREC_SEMANTICS_CONFIRMED),
               codigo={p.name: sha(p) for p in code},
               salidas={str(p.relative_to(OUT)).replace("\\", "/"): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in outs},
               fuentes_sha256={f"{a}/{b}": e for a, b, _, _, e in fu})
    (OUT / "metadata/manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(log))
    print(val[["prueba", "resultado", "registros_afectados", "severidad"]].to_string())


if __name__ == "__main__":
    main(skip_extract="--skip-extract" in sys.argv)
