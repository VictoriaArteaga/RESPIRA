# Reglas de transformación (pipeline 1.0.0)

Todas las reglas provienen de las decisiones aprobadas en la quinta auditoría; están parametrizadas en `data/scripts/pipeline/respira_datasets/config.py`.

## SIVIGILA / V1
- Fuente: `Datos_{año}_995.xlsx`, hoja de detalle por año (ver `fuentes_utilizadas.csv`). Se leen solo campos no personales; se excluyen diligencia, cargo, teléfono, correo, NIT y nombre de UPGD.
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
