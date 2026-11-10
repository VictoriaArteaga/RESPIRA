"""Validaciones automáticas reproducibles (17 obligatorias + control contra el piloto).

Cada prueba devuelve: nombre, resultado (PASS/FAIL/WARN/INFO), registros_afectados, severidad, observacion, accion.
Los hallazgos NO se ocultan ni se corrigen modificando datos: se informan.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config as C
from .supervised import VARIANTS, offset_validity, _positions

REF = dict(grid=36736, completas=34224, grupos_repetidos=827, filas_repetidas=1705, incongruentes=10,
           municipios_temp=11, semanas_temp=5724, pob=704)


def _r(n, res, afect, sev, obs, acc):
    return dict(prueba=n, resultado=res, registros_afectados=int(afect), severidad=sev, observacion=obs, accion_tomada=acc)


def run_all(ctx: dict) -> pd.DataFrame:
    v1, v2, v3 = ctx["v1"], ctx["v2"], ctx["v3"]
    rows, pop, sup = ctx["rows"], ctx["pop"], ctx["supervised"]
    out = []
    K = ["codigo_municipio", "anio", "semana_epidemiologica"]
    # 1 unicidad
    dups = {n: int(d.duplicated(K).sum()) for n, d in (("V1", v1), ("V2", v2), ("V3", v3), ("V2_tmp_valida", ctx["v2_valida"]))}
    for n, t in sup.items():
        dups[f"sup:{n}"] = int(t.duplicated(K).sum())
    out.append(_r("01_unicidad_llave_municipio_anio_semana", "PASS" if sum(dups.values()) == 0 else "FAIL", sum(dups.values()),
                  "CRITICA", f"Duplicados por tabla: {dups}", "Ninguna (sin duplicados)" if sum(dups.values()) == 0 else "Revisar construcción"))
    # 2 cobertura territorial y temporal
    nmun, nyr, n = v1.codigo_municipio.nunique(), v1.anio.nunique(), len(v1)
    ok = (nmun == 64 and nyr == 11 and n == REF["grid"])
    out.append(_r("02_cobertura_territorial_y_temporal", "PASS" if ok else "FAIL", 0 if ok else abs(n - REF["grid"]), "CRITICA",
                  f"{nmun} municipios, {nyr} años (2012-2022), {n} filas; referencia {REF['grid']} (64 x 574; semana 53 en 2014 y 2020).", "Cuadrícula completa conservada"))
    # 3 conteos por año y municipio
    por_anio = v1.groupby("anio").size()
    esperado = pd.Series({y: 64 * C.WEEKS_IN_YEAR[y] for y in C.YEARS})
    bad_y = int((por_anio != esperado).sum()); bad_m = int((v1.groupby("codigo_municipio").size() != 574).sum())
    out.append(_r("03_conteos_por_anio_y_municipio", "PASS" if bad_y + bad_m == 0 else "FAIL", bad_y + bad_m, "ALTA",
                  f"Años con conteo distinto del esperado: {bad_y}; municipios distintos de 574 semanas: {bad_m}.", "Ninguna"))
    # 4 negativos o imposibles
    neg = int((rows[["iracext_1", "iracext_2", "iracext_3", "totcext_1", "totcext_2", "totcext_3"]] < 0).any(axis=1).sum())
    _ic = rows[["iracext_1", "iracext_2", "iracext_3"]]
    nonint = int((((_ic % 1) != 0) & _ic.notna()).any(axis=1).sum())
    pop_bad = int((pop.poblacion_menor_5 <= 0).sum())
    ira_gt_tot = int((v1.iracext_0_4_notificado_suma > v1.totcext_0_4_experimental_suma).sum())
    nonnum = int(rows["_raw_nonnumeric"].sum())
    clim_neg = int(((v2[["temperatura_min_semanal"]] < -30).sum()).sum() + (v2["temperatura_max_semanal"] > 50).sum())
    tot = neg + nonint + pop_bad + nonnum + clim_neg
    out.append(_r("04_valores_negativos_o_imposibles", "PASS" if tot == 0 else "FAIL", tot, "ALTA",
                  f"Registros con conteos negativos: {neg}; no enteros: {nonint}; texto no numérico en campos numéricos: {nonnum}; población <=0: {pop_bad}; temperaturas fuera de [-30,50]: {clim_neg}. "
                  f"Municipio-semanas con IRA > consultas totales (experimental): {ira_gt_tot} (informativo).", "Sin cambios; se informa" if tot else "Ninguna"))
    # 5 campos faltantes
    parc = int((v1.estado_dato_ira == "PARCIAL_VACIOS").sum())
    out.append(_r("05_campos_faltantes", "WARN" if parc else "PASS", parc, "MEDIA",
                  f"{parc} municipio-semanas con algún componente iracext_1..3 vacío en al menos un registro ({int((~rows.fila_ira_completa).sum())} registros). Se dejan NULL (PARCIAL_VACIOS).",
                  "Marcados como PARCIAL_VACIOS; sin imputación"))
    # 6 semanas ausentes
    aus = int((v1.estado_dato_ira == "AUSENTE").sum()); comp = int((v1.estado_dato_ira == "COMPLETO").sum())
    out.append(_r("06_semanas_ausentes", "WARN" if aus else "PASS", aus, "MEDIA",
                  f"{aus} municipio-semanas AUSENTES (sin registro). Semanas COMPLETAS: {comp} (referencia auditoría: {REF['completas']}; diferencia {comp - REF['completas']:+d}). "
                  f"Parciales: {parc}.", "Conservadas como NULL con estado AUSENTE; no se convierten en cero"))
    # 7 registros repetidos
    g = rows[rows.es_repetido]
    ng, nf = g.grupo_clave.nunique(), len(g)
    yrs = sorted(g.anio.unique().tolist())
    ok7 = (ng == REF["grupos_repetidos"] and nf == REF["filas_repetidas"])
    out.append(_r("07_registros_repetidos", "PASS" if ok7 else "WARN", nf, "ALTA",
                  f"{ng} grupos / {nf} filas repetidos (referencia {REF['grupos_repetidos']}/{REF['filas_repetidas']}); años afectados: {yrs}. "
                  f"Grupos con orden de último reporte NO determinable: {int(g[~g.ultimo_determinable].grupo_clave.nunique())}.",
                  "Todas las filas conservadas; SUMA y ULTIMO_REPORTE lado a lado; ninguna es oficial"))
    # 8 diferencias SUMA vs ULTIMO
    a, b = v1.iracext_0_4_notificado_suma, v1.iracext_0_4_notificado_ultimo_reporte
    both = a.notna() & b.notna()
    diff = int((both & (a != b)).sum())
    byy = v1[both].assign(d=(a - b)[both]).groupby("anio").d.sum().to_dict()
    out.append(_r("08_diferencias_suma_vs_ultimo_reporte", "INFO", diff, "MEDIA",
                  f"{diff} municipio-semanas con SUMA != ULTIMO_REPORTE (ambos calculables); diferencia total SUMA-ULTIMO por año: { {int(k): int(x) for k, x in byy.items() if x} }. Municipio-semanas con último no determinable: {int((v1.estado_dato_ira_ultimo_reporte=='NO_DETERMINABLE').sum())}.",
                  "Ambas variantes conservadas como escenarios de sensibilidad; nunca como predictores simultáneos"))
    # 9 consistencia territorial
    flagged = rows[rows.territorio_incongruente]
    unass = rows[~rows.codigo_asignable]
    out.append(_r("09_consistencia_codigos_territoriales", "WARN" if len(flagged) else "PASS", len(flagged), "MEDIA",
                  f"{len(flagged)} registros con código/departamento incongruente (referencia {REF['incongruentes']}): {flagged.motivo_territorial.value_counts().to_dict()}. "
                  f"{len(unass)} registro(s) con código no asignable a la cuadrícula (excluidos de V1, conservados en rechazados). Códigos NO corregidos. "
                  f"Municipio-semanas afectados en V1: {int(v1.tiene_codigo_territorial_incongruente.sum())}.", "Bandera tiene_codigo_territorial_incongruente; sin corrección"))
    # 10 población
    comb = pop.drop_duplicates(["codigo_municipio", "anio"]).shape[0]
    falta = int(v1.poblacion_menor_5.isna().sum())
    inconsist = int((pop.poblacion_menor_5 != pop._suma_hombres_mujeres).sum())
    out.append(_r("10_correspondencia_poblacion_municipio_anio", "PASS" if (comb == REF["pob"] and falta == 0 and inconsist == 0) else "FAIL", falta + inconsist, "ALTA",
                  f"{comb}/{REF['pob']} combinaciones municipio-año DANE; filas V1 sin población: {falta}; total_0..4 != hombres+mujeres: {inconsist}. Salto 2017->2018 sin reescalar (dane_libro distingue).",
                  "Valores originales conservados"))
    # 11 cobertura climática real
    t_ok = v2[v2.estado_calidad_temperatura == "VALIDO"]
    p_ok = v3[v3.estado_calidad_precipitacion == "CANDIDATA_7DE7_SEMANTICA_PENDIENTE"]
    n_t_mun = t_ok.codigo_municipio.nunique(); n_p_mun = p_ok.codigo_municipio.nunique()
    t_c = int(((v2.estado_calidad_temperatura == "VALIDO") & (v2.estado_dato_ira == "COMPLETO")).sum())
    out.append(_r("11_cobertura_real_temperatura_y_precipitacion", "INFO", len(t_ok), "MEDIA",
                  f"Temperatura VALIDA: {len(t_ok)} municipio-semanas en {n_t_mun} municipios ({t_c} con IRA SUMA completa); referencia auditoría: {REF['municipios_temp']} municipios / {REF['semanas_temp']} semanas con calendario borrador de 11 años. "
                  f"Diferencia: V2 solo vincula años con calendario verificado (2016, 2022). Precipitación candidata 7/7: {len(p_ok)} municipio-semanas en {n_p_mun} municipios (semántica pendiente).",
                  "Cobertura recalculada con las reglas aprobadas"))
    # 12 Aldana
    ald_v = v2[v2.codigo_municipio == "52022"]
    viol = int(ald_v[[f"{k}_semanal" for k in C.TEMP_VARS]].notna().sum().sum())
    out.append(_r("12_exclusion_aldana_52055230_temperatura", "PASS" if viol == 0 and (ald_v.estado_calidad_temperatura == "SERIE_NO_CONFIABLE").all() else "FAIL", viol, "CRITICA",
                  f"Evidencia recalculada: {ctx['evid']['aldana']}. Valores de temperatura en Aldana: {viol}.", "Excluidas las 3 variables; estado SERIE_NO_CONFIABLE"))
    # 13 Chachagüí
    ch = v2[v2.codigo_municipio == C.CHACHAGUI_MUN]
    viol = int(ch[[f"{k}_semanal" for k in C.TEMP_VARS]].notna().sum().sum())
    out.append(_r("13_estado_pendiente_chachagui", "PASS" if viol == 0 and (ch.estado_calidad_temperatura == "SIN_ESTACION_VALIDADA").all() else "FAIL", viol, "ALTA",
                  f"Evidencia: {ctx['evid']['chachagui']}. Valores de temperatura asociados: {viol}.", "Asociación excluida de V2; SIN_ESTACION_VALIDADA; V1 y demás municipios no afectados"))
    # 14 calendarios no verificados
    nv = v1[v1.calendar_verificado == "NO"]
    viol = int(nv.semana_inicio.notna().sum() + v2.loc[v2.calendar_verificado == "NO", [f"{k}_semanal" for k in C.TEMP_VARS]].notna().sum().sum()
               + v3.loc[v3.calendar_verificado == "NO", "n_dias_precipitacion_candidata"].notna().sum())
    out.append(_r("14_calendarios_no_verificados", "PASS" if viol == 0 else "FAIL", len(nv), "ALTA",
                  f"{len(nv)} filas ({nv.anio.nunique()} años) con calendar_verificado=NO; verificados: {sorted(C.CALENDAR_VERIFIED)}. Fechas/valores climáticos en años no verificados: {viol}.", "Año y semana SIVIGILA conservados; sin fechas inventadas ni vínculo IDEAM"))
    # 15 sin imputación
    ira_nonnull_incompleto = int((v1.iracext_0_4_notificado_suma.notna() & (v1.estado_dato_ira != "COMPLETO")).sum())
    t_bad = int(sum(((v2[f"n_dias_{k}"] < C.TEMP_MIN_DAYS) & v2[f"{k}_semanal"].notna()).sum() for k in C.TEMP_VARS))
    # recálculo independiente de la suma desde las filas originales
    chk = rows[rows.codigo_asignable & rows.fila_ira_completa].groupby(["cod_mun", "anio", "semana"]).ira_fila.sum()
    m = v1[v1.estado_dato_ira == "COMPLETO"].set_index(["codigo_municipio", "anio", "semana_epidemiologica"]).iracext_0_4_notificado_suma
    m.index.names = ["cod_mun", "anio", "semana"]
    recalc = int((m != chk.reindex(m.index)).sum())
    out.append(_r("15_ausencia_de_valores_imputados", "PASS" if ira_nonnull_incompleto + t_bad + recalc == 0 else "FAIL", ira_nonnull_incompleto + t_bad + recalc, "CRITICA",
                  f"IRA no nula en semana no completa: {ira_nonnull_incompleto}; temperatura con <6 días y valor: {t_bad}; SUMA distinta del recálculo independiente desde registros: {recalc}.", "Ninguna imputación/interpolación en el pipeline"))
    # 16 sin ceros generados
    aus_mask = v1.estado_dato_ira == "AUSENTE"
    zeros_gen = int((aus_mask & (v1.iracext_0_4_notificado_suma.notna() | v1.iracext_0_4_notificado_ultimo_reporte.notna() | v1.totcext_0_4_experimental_suma.notna())).sum())
    zeros_real = int((v1.iracext_0_4_notificado_suma == 0).sum())
    out.append(_r("16_ausencia_de_ceros_generados", "PASS" if zeros_gen == 0 else "FAIL", zeros_gen, "CRITICA",
                  f"Semanas ausentes con valor numérico: {zeros_gen}. Ceros presentes en V1 (SUMA): {zeros_real}, todos provienen de registros con cero reportado (numero_reportes>0: {int(((v1.iracext_0_4_notificado_suma == 0) & (v1.numero_reportes > 0)).sum())}).",
                  "Ausente = NULL"))
    # 17 fugas temporales
    leak = 0; detalles = []
    P = _positions().set_index(["anio", "semana_epidemiologica"])["pos"]
    for name, t in sup.items():
        variant = t["interpretacion_reportes"].iloc[0]; col = VARIANTS[variant][0]; h = int(t["horizonte_semanas"].iloc[0])
        base = v1.assign(pos=pd.MultiIndex.from_frame(v1[["anio", "semana_epidemiologica"]]).map(P)).set_index(["codigo_municipio", "pos"])[col]
        bad = 0
        for k in C.LAGS:
            x = t[t[f"ira_lag{k}"].notna()]
            ref = base.reindex(pd.MultiIndex.from_arrays([x.codigo_municipio, x.posicion_secuencial - k])).to_numpy()
            bad += int((x[f"ira_lag{k}"].to_numpy() != ref).sum())
            bad += int(((x.posicion_secuencial - k) > x.posicion_secuencial).sum())   # un rezago nunca es posterior a t
        x = t[t[f"target_ira_t_plus_{h}"].notna()]
        ref = base.reindex(pd.MultiIndex.from_arrays([x.codigo_municipio, x.posicion_secuencial + h])).to_numpy()
        bad += int((x[f"target_ira_t_plus_{h}"].to_numpy() != ref).sum())
        # el objetivo debe ser estrictamente posterior y no cruzar transiciones no validadas
        tp = x.anio_objetivo.map(lambda a: a).astype(int) * 100 + x.semana_objetivo.astype(int)
        bad += int((tp <= x.anio * 100 + x.semana_epidemiologica).sum())
        cross = x.anio_objetivo != x.anio
        bad += int((cross & ~x.anio.isin(list(C.CALENDAR_VERIFIED))).sum())
        for k in C.LAGS:
            y = t[t[f"ira_lag{k}"].notna()]
            ypos = y.posicion_secuencial - k
            yy = ypos.map(_positions().set_index("pos")["anio"])
            bad += int(((yy != y.anio) & ~yy.isin(list(C.CALENDAR_VERIFIED))).sum())
        leak += bad; detalles.append(f"{name}:{bad}")
    out.append(_r("17_ausencia_de_fugas_temporales_supervisadas", "PASS" if leak == 0 else "FAIL", leak, "CRITICA",
                  f"Verificación independiente de rezagos (solo pasado), objetivos (solo futuro) y transiciones de año; violaciones por tabla: {', '.join(detalles)}.", "Ninguna fuga; sin entrenamiento ni métricas"))
    # extra: control contra el piloto exploratorio (golden file de 312 filas)
    out.append(ctx["pilot_check"])
    return pd.DataFrame(out)
