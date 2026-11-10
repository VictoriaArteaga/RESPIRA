"""Documentos de metadatos generados con cifras reales de la corrida."""
from __future__ import annotations
from . import config as C


def write_all(meta_dir, x: dict):
    v1, v2, v3, val = x["v1"], x["v2"], x["v3"], x["val"]
    n_t = len(x["v2_valida"])
    mun_t = x["v2_valida"].codigo_municipio.nunique()
    st2 = x["mstat2"].estado_calidad_temperatura.value_counts().to_dict()
    st3 = x["mstat3"].estado_calidad_precipitacion.value_counts().to_dict()
    comp = int((v1.estado_dato_ira == "COMPLETO").sum())
    (meta_dir / "reglas_transformacion.md").write_text(f"""# Reglas de transformación (pipeline {C.PIPELINE_VERSION})

Todas las reglas provienen de las decisiones aprobadas en la quinta auditoría; están parametrizadas en `data/scripts/pipeline/respira_datasets/config.py`.

## SIVIGILA / V1
- Fuente: `Datos_{{año}}_995.xlsx`, hoja de detalle por año (ver `fuentes_utilizadas.csv`). Se leen solo campos no personales; se excluyen diligencia, cargo, teléfono, correo, NIT y nombre de UPGD.
- Se conservan registros con `cod_mun` 52xxx o `ndep_notif` = NARIÑO. Códigos territoriales NO se corrigen.
- Indicador `iracext_0_4_notificado` = `iracext_1+iracext_2+iracext_3` (conteo notificado; no incidencia, no pacientes únicos).
- Si un registro tiene algún componente vacío su valor es NULL (PARCIAL_VACIOS); el municipio-semana es NULL si algún registro que contribuye está incompleto. Sin registros: AUSENTE (NULL, nunca 0).
- Grupo de repetición: mismo año + municipio + semana + UPGD (`cod_pre` sin ceros) + sede (`cod_sub`). Todas las filas se conservan.
  - `SUMA`: suma de todos los registros del municipio-semana.
  - `ULTIMO_REPORTE`: por grupo, el registro de mayor `NUM_CON`. Si `NUM_CON` falta o el máximo no es único, el orden no es verificable: NO_DETERMINABLE (NULL).
  - Ninguna es la oficial; no deben usarse juntas como predictores.
- Cuadrícula: 64 municipios x 574 semanas (52 por año; 53 en 2014 y 2020, años en los que SIVIGILA reporta semana 53). Es la llave reportada, no una verificación de calendario.
- Población: suma `Total_0..4` (área Total) de los libros DANE; valores originales, `dane_libro` indica la serie. El salto 2017->2018 NO se ajusta.
- `regimen`: PRE_PANDEMIA <=2019, PANDEMIA 2020-2021, POST_PANDEMIA 2022. 2021 con `completitud_no_verificada=TRUE`.
- Proporciones IRA/`totcext` son EXPERIMENTALES (denominador sin confirmar por el INS). No se calculan tasas ni incidencias.

## Calendario
- Verificados: 2016 y 2022 (boletines INS, SE52 = 25-31 dic; semanas domingo-sábado enumeradas hacia atrás). Los demás años: `calendar_verificado=NO`, sin fechas y sin vínculo con IDEAM.

## IDEAM / V2 (temperatura)
- Estación solo del mismo municipio (campo Municipio del catálogo, tabla `reports/estaciones_candidatas_ideam.csv`; mapeo manual de Tumaco, El Tablón y Santa Cruz). Sin vecinas ni interpolación.
- Semana domingo-sábado del calendario verificado; mínima = mínimo de `TSSM_MN_D`, máxima = máximo de `TSSM_MX_D`, media = media de `TSSM_MEDIA_D`, usando solo días válidos; se exige >=6/7 días por variable; se guarda `n_dias`.
- Elegibilidad de estación: >=80% de las semanas verificadas (104) con >=6/7 días en las tres variables.
- Aldana (52055230): excluida (SERIE_NO_CONFIABLE). Chachagüí (52045020): SIN_ESTACION_VALIDADA.

## IDEAM / V3 (precipitación, candidata)
- `PTPM_CON_INTER` tiene semántica y unidad pendientes: no se suma, no se llama precipitación validada y no es predictor. Se conserva el valor original diario (`v3/precipitacion_diaria_candidata_preparacion.csv`) y el número de días por semana (7/7 como requisito futuro). Interruptor `PREC_SEMANTICS_CONFIRMED` en `build_climate.py` (False).

## Supervisadas
- Rezagos 1-4 y objetivos t+2, t+3 por posición en la malla; solo se calculan sin cruzar una transición de año no validada (Y->Y+1 válida solo si Y está verificado: únicamente 2016->2017). Motivo explícito cuando es NULL. Sin entrenamiento ni métricas.
- Partición temporal recomendada (futura): bloques cronológicos, p. ej. entrenar 2012-2018, validar 2019, probar 2022; 2020-2021 como periodo de estrés o excluido por experimento; umbrales y escaladores solo con el bloque de entrenamiento; sin mezcla aleatoria de semanas; no usar SUMA y ULTIMO_REPORTE simultáneamente.
""", encoding="utf-8")

    (meta_dir / "limitaciones_dataset.md").write_text(f"""# Limitaciones (qué impide usar registros para entrenamiento)

Estados: **construido** (archivos generados) ≠ **calidad suficiente** ≠ **habilitado para entrenamiento**. Ningún dataset está habilitado para entrenamiento.

1. **Significado del indicador** (INS pendiente): conteo notificado; no es incidencia ni pacientes únicos; el denominador `totcext` no está confirmado.
2. **Reportes repetidos 2012-2018** (INS pendiente): SUMA vs ULTIMO_REPORTE sin interpretación oficial; {int((v1.estado_orden_ultimo_reporte=='NO_DETERMINABLE').sum())} municipio-semanas con último reporte no determinable.
3. **Calendario**: solo 2016 y 2022 verificados. Las semanas de los otros años no pueden vincularse a fechas ni a IDEAM; las secuencias que cruzan transiciones no validadas quedan sin rezago/objetivo.
4. **2021**: completitud no verificada (conteo oficial INS pendiente). 2020-2021 régimen pandémico.
5. **Ausencias**: {int((v1.estado_dato_ira=='AUSENTE').sum())} municipio-semanas ausentes y {int((v1.estado_dato_ira=='PARCIAL_VACIOS').sum())} con vacíos; no imputados.
6. **Territorial**: registros con código/departamento incongruente conservados con bandera; registros con departamento NARIÑO y código ajeno o vacío no asignables (ver `v1/registros_territoriales_marcados.csv`).
7. **Población DANE**: salto de serie 2017->2018 sin ajustar; no existe empalme oficial.
8. **Temperatura (V2)**: solo años 2016 y 2022; {n_t} municipio-semanas válidas en {mun_t} municipios. Representatividad de la estación para el municipio no validada; ubicación municipal solo por campo del catálogo; Chachagüí sin estación validada; Aldana excluida; series IDEAM sin banderas de calidad.
9. **Precipitación (V3)**: `PTPM_CON_INTER` con significado/unidad pendientes (IDEAM). V3 no contiene precipitación validada.
10. **Tamaño**: muchos municipios tienen medianas semanales bajas (<10), lo que limita la estabilidad de cualquier modelo.

## Qué se necesita para habilitar la versión validada
- INS: interpretación de reportes repetidos, significado de `iracext/totcext`, calendario epidemiológico oficial 2012-2022, conteo oficial 2021.
- IDEAM: significado y unidad de `PTPM_CON_INTER`, banderas de calidad, revisión de la estación 52055230, municipio de ubicación de 52045020.
- DANE: empalme de las series 2005-2017 y 2018-2042.
- Límites municipales (IGAC/DANE) para verificar la ubicación de estaciones.
""", encoding="utf-8")

    sv = {k: int(t.fila_completa_ira.sum()) for k, t in x["sup"].items()}
    (meta_dir / "bitacora_construccion.md").write_text(f"""# Bitácora de construcción

- Pipeline `{C.PIPELINE_VERSION}`; calendario `{C.CALENDAR_VERSION}`. Fuentes leídas en solo lectura desde `{C.SOURCE_DIR}`.
- Etapa 1 (lectura): SIVIGILA 2012-2022 (hoja de detalle por año) y DANE 2005-2017 / 2018-2042 a `data/interim/` (regenerable, ignorado por git).
- Etapa 2: normalización y banderas territoriales; grupos de repetición ({int(x['siv'].es_repetido.sum())} filas, {x['siv'][x['siv'].es_repetido].grupo_clave.nunique()} grupos); agregación municipio-semana; población; V1.
- {x['log'][0]}; {x['log'][1]}.
- Estados municipales de temperatura: {st2}. Estados de precipitación: {st3}.
- Evidencia Aldana: {x['evid']['aldana']}. Evidencia Chachagüí: {x['evid']['chachagui']}.
- Filas completas (t, lags, objetivo) por tabla supervisada: {sv}.
- Validaciones: {int((val.resultado=='PASS').sum())} PASS, {int((val.resultado=='WARN').sum())} WARN, {int((val.resultado=='FAIL').sum())} FAIL, {int((val.resultado=='INFO').sum())} INFO (ver `validaciones.csv`).
- No se modificaron fuentes; no hubo imputación; no hubo conexión a PostgreSQL/Supabase; no se entrenó ningún modelo; no se hicieron commits.
""", encoding="utf-8")
