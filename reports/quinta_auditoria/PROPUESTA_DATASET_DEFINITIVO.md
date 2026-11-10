# Propuesta de organización definitiva de los datos

**Fecha:** 5 de noviembre de 2026. **Estado:** propuesta para discusión; no se creó ninguna carpeta, tabla ni archivo de datos fuera de `reports/quinta_auditoria/`. No cambia la arquitectura de la aplicación ni el esquema PostgreSQL.

## 1. Principios

1. **Lo original no se toca.** Cada nivel se genera a partir del anterior mediante un script versionado; nunca se edita a mano.
2. **No se pierden filas en los niveles de normalización y validación.** Se marcan, no se eliminan.
3. **Ausente ≠ cero.** Una semana sin fila, un vacío o una cobertura insuficiente son `NA` con un motivo.
4. **Cada decisión metodológica pendiente es un parámetro versionado**, no una constante escondida en el código. Dos variantes de consolidación pueden coexistir como columnas hasta que se apruebe una.
5. **Todo valor es rastreable** hasta archivo, hoja, fila (o estación-fecha), hash y versión de la transformación.
6. **Lo sintético vive aparte** y lleva siempre una marca visible.

Esta propuesta es compatible con la Fase 2.2 ya implementada (`docs/data-integration/README.md`): las tablas `data_source`, `import_batch`, `sivigila_report` (con repeticiones marcadas `unresolved_repeat` y vacío = NULL), `climate_observation` y `annual_population` corresponden a los niveles 1–2 de abajo. Los niveles 3–5 son archivos derivados fuera de la base. No se auditó el código de los importadores ni se ejecutó ninguna carga.

## 2. Niveles

| Nivel | Nombre | Contenido | ¿Mutable? | Ubicación propuesta | Trazabilidad |
|---:|---|---|---|---|---|
| 0 | **Fuentes originales** | Los archivos tal como se recibieron: `Datos_{año}_995.xlsx`, libros DANE, catálogo y `.data` IDEAM | **Nunca** (solo lectura) | `data/00_originales/{fuente}/…` (ignorado por git) + `MANIFEST.csv` | Nombre original, proveedor, URL, fecha de descarga, bytes, SHA-256, licencia |
| 1 | **Normalizados** | Una fila fuente = una fila normalizada; tipos y formatos corregidos (DIVIPOLA como texto de 5 dígitos, `cod_pre` sin ceros iniciales, fechas ISO, vacío = NULL). Sin filtrar, sin sumar | Regenerable | `data/10_normalizados/` (o tablas `sivigila_report`, `climate_observation`, `annual_population`) | `source_file`, `source_sha256`, `sheet`, `source_row`, `transformation_version` en cada fila |
| 2 | **Validados** | Nivel 1 + banderas de validación (no cambian valores): código/departamento incongruente, vacío en numerador, semana 53, grupo repetido, valor fuera de rango, serie sin unidad confirmada | Regenerable | `data/20_validados/` (o `data_quality_issue`) | `validation_rule_id`, `severity`, `status` |
| 3 | **Derivados** | Agregaciones reproducibles: SIVIGILA por municipio-semana (variantes de consolidación lado a lado); IDEAM diario→semanal con `n_dias`; población anual; tablas de referencia (calendario epidemiológico por año, estación→municipio) | Regenerable | `data/30_derivados/` | `derivation_id`, parámetros (umbral 6/7, regla de repetición, calendario), versión |
| 4 | **Dataset analítico** | Unión final: una fila por municipio × semana epidemiológica, con malla completa (ver sección 4). Es el dataset «definitivo» de análisis | Congelado por versión | `data/40_analitico/respira_analitico_v{N}.csv` + `.json` de metadatos | Hash de cada insumo nivel 3, versión del script, fecha |
| 5 | **Dataset de entrenamiento** | Recorte del nivel 4 para un experimento: definición de objetivo, ventana de variables, particiones temporales, filas excluidas con motivo | Congelado por experimento | `data/50_entrenamiento/{experimento}/` | Hash del nivel 4, definición de partición, semilla, lista de exclusiones |
| — | **Sintéticos y pruebas** | `backend/data/simulated/ira_cases.csv`, SQLite de demostración | Fuera de la cadena | donde están | Columna `data_source = SINTÉTICO` |

Los archivos existentes `data/processed/pilot/piloto_respira_2016_2022.csv` y `reports/cuarta_auditoria/…_v2.csv` se conservarían como **referencia de pruebas** («golden file»): la nueva cadena debe reproducir sus 312 filas, como se hizo a mano en esta auditoría.

## 3. Nombres, versiones y hashes

- **Nombre de archivo:** `{fuente}__{contenido}__{periodo}__v{MAYOR.MENOR}.{ext}`; p. ej. `sivigila995__municipio_semana__2012-2022__v1.0.csv`.
- **Metadatos laterales (`.json` junto a cada archivo derivado):** `dataset_id`, `nivel`, `version`, `fecha`, `insumos` (lista de archivo + SHA-256), `script` (ruta + commit), `parametros` (reglas vigentes), `filas`, `sha256`.
- **`MANIFEST.csv` del nivel 0:** `archivo, proveedor, url, fecha_descarga, bytes, sha256, hojas, filas_con_datos, nota`. El Anexo B de `INFORME_GENERAL.md` es una primera línea base para 14 archivos.
- **Cambio de datos o de regla ⇒ nueva versión.** Las versiones anteriores no se sobrescriben.
- **Cada fila del nivel 4** lleva `analitico_version` y `calendar_version`.

## 4. Dataset analítico: diseño

**Unidad:** municipio (DIVIPOLA) × semana epidemiológica (año epi, semana).
**Malla:** completa (64 × 574 = 36.736 filas para 2012–2022). Las filas sin datos permanecen con estado `AUSENTE`; no se eliminan ni se rellenan.
**Campos en tres bloques** (sufijo indica estado de decisión):

| Bloque | Columnas principales |
|---|---|
| Llaves y calendario | `divipola`, `municipio`, `anio_epi`, `semana_epi`, `semana_inicio`, `semana_fin`, `calendar_version` |
| SIVIGILA | `n_filas_fuente`, `n_upgd`, `n_grupos_repetidos`, `ira_0_4_suma` (todas las filas), `ira_0_4_ultimo_reporte` (por grupo de mayor `NUM_CON`), `ira_vacio_componente` (bandera), `consultas_0_4_totales` (`totcext_1..3`, *pendiente de validar*), `ajuste_7_en_semana` (bandera), `sivigila_estado` (`PRESENTE`, `PARCIAL_VACIOS`, `AUSENTE`) |
| IDEAM (V2) | `est_temp_codigo`, `est_temp_altitud_m`, `est_temp_estado_catalogo`, `tmin_sem`, `tmax_sem`, `tmedia_sem`, `n_dias_tmin`, `n_dias_tmax`, `n_dias_tmedia`, `temp_estado` (`VALIDO`, `INSUFICIENTE`, `SIN_ESTACION`, `SERIE_NO_CONFIABLE`), `regla_suficiencia` |
| IDEAM (V3) | `est_prec_codigo`, `prec_suma_sem`, `n_dias_prec`, `prec_estado`, `n_dias_prec_gt135` |
| DANE | `pob_0_4`, `dane_libro`, `dane_anio`, `dane_sha256` |
| Trazabilidad | `src_sivigila_archivo`, `src_sivigila_sha256`, `src_ideam_archivos`, `transformation_version`, `analitico_version` |

**No incluye:** tasas, proporciones ni variables derivadas de decisiones sin aprobar; esas se calculan en el nivel 5.

**Versiones propuestas:**

| Versión | Alcance | Filas con IRA completa (aprox.) | Prerrequisitos |
|---|---|---:|---|
| **V1 (núcleo epidemiológico + demografía)** | 64 municipios, 2012–2022 | 34.224 de 36.736 | Decisiones 1, 2, 5, 6, 7, 8, 10 |
| **V2 (V1 + temperatura)** | Igual malla; temperatura en 12 municipios (11 si se excluye Aldana) | 6.282 con temperatura completa | + decisiones 3, 4, 9 |
| **V3 (V2 + precipitación)** | + 38 municipios con precipitación | 19.934 con precipitación completa | + confirmación IDEAM de `PTPM_CON_INTER` y unidad |

Las decisiones están numeradas en la sección 9 de `INFORME_GENERAL.md`.

## 5. Dataset de entrenamiento: diseño

Se construye por experimento, nunca se edita el nivel 4. Cada experimento define y congela:

- **Objetivo** (conteo, proporción o alerta) y horizonte (1–4 semanas).
- **Ventana de variables:** solo rezagos observados en t, t−1, …; nunca valores posteriores al momento de predicción.
- **Partición temporal por bloques:** entrenar 2012–2018 → validar 2019 → probar 2022 (2020–2021 como estrés o excluidos, según decisión 5). Sin partición aleatoria.
- **Umbrales y normalizaciones calculados solo con el bloque de entrenamiento.**
- **Lista de filas excluidas con motivo** (sin estación, cobertura insuficiente, semana ausente).
- **Referencias base** (misma semana del año anterior; modelo estacional simple) que el experimento debe superar.

## 6. Reglas de normalización por fuente (nivel 1)

| Fuente | Regla |
|---|---|
| SIVIGILA | Leer por **nombre de columna** (los libros difieren entre años). Quedarse con `cod_eve = 995`. Hoja de detalle por año (Anexo del informe). `cod_mun` → texto 5 dígitos; `cod_pre`/`cod_sub` → texto sin ceros iniciales; fechas seriales y texto → ISO; vacío → NULL (no 0). Registrar hoja y fila Excel. No copiar `diligencia`, `cargo`, `telefono`, `correo`. No sumar hojas alternativas (`Base Recibida` 2012, `Hoja1` 2019). |
| IDEAM | `{VARIABLE}@{ESTACION}.data`, separador `|`, fecha con sello 07:00. Un registro por (estación, variable, fecha); informar fechas duplicadas, no corregirlas. Asignar estación→DIVIPOLA mediante una tabla de referencia versionada (no por nombre dentro del código). |
| DANE | Armonizar los dos libros por **nombre de columna**. Filtrar `Área = Total`. Población 0–4 = suma de `Total_0..4`. `MPIO` → texto de 5 dígitos. Registrar libro y hash. |

## 7. Qué hacer con el piloto

- **Conservar** `piloto_respira_2016_2022.csv` y su versión v2 sin cambios, como archivos de referencia.
- **No ampliar el CSV existente.** Reconstruir con la cadena de niveles y comprobar que las 312 filas de 2016/2022 de los tres municipios coinciden con el piloto (en esta auditoría coinciden al 100%).
- **Decidir un solo nombre** para el indicador (decisión 10).

## 8. Orden de trabajo sugerido (cuando se aprueben las decisiones)

1. Aprobar decisiones de la sección 9 de `INFORME_GENERAL.md` y enviar las consultas externas (sección 9 abajo).
2. Crear `MANIFEST.csv` y guardar los originales en un directorio de solo lectura.
3. Tabla de referencia: calendario epidemiológico por año (con fuente INS) y estación→municipio.
4. Normalización SIVIGILA/IDEAM/DANE + validaciones (alineadas con `backend/app/importers`).
5. Derivados: agregación semanal y variantes de consolidación lado a lado.
6. Dataset analítico V1; prueba automática contra el piloto; revisión.
7. V2 (temperatura) y, tras la confirmación de IDEAM, V3.
8. Primer experimento exploratorio con las referencias base.

**Criterios de aceptación mínimos de V1:** 36.736 filas; llave única; ninguna fila eliminada; ceros solo donde la fuente trae un cero; coincide con el piloto en sus 312 filas; hashes y versiones en todas las filas; informe de cobertura por municipio y año.

## 9. Consultas externas recomendadas

| A | Pregunta | Para resolver |
|---|---|---|
| INS / Secretaría de Salud de Nariño | ¿Un reporte posterior de la misma UPGD y semana (mayor `NUM_CON`) reemplaza, corrige o complementa al anterior? ¿Por qué hay reportes con el mismo `NUM_CON`? ¿Qué significa `ajuste = 7` en el evento 995? ¿Los `totcext_*` son consultas totales (denominador)? ¿«Consultas», «atenciones» o «pacientes»? ¿Por qué hay semanas sin fila (Chachagüí SE44/52 y Funes SE11/21 de 2016; Francisco Pizarro en 2020)? Calendario epidemiológico oficial de 2012–2023. Conteo oficial de filas del evento 995 en 2021 (y las 39 filas con semana 53). | D-01, D-02, D-06, D-07, D-09, D-11 |
| IDEAM | Significado y unidad de `PTPM_CON_INTER`; banderas y nivel de aprobación de las series diarias; revisión de la estación 52055230 (Aldana, mín = máx); representatividad de estaciones; día pluviométrico en la fecha de la serie | D-03, D-04, D-05 |
| DANE | Empalme oficial entre la serie 2005–2017 y la 2018–2042; disponibilidad del libro nacional/departamental | D-15 |

## 10. Alternativas si la decisión de alcance cambia

- **Alcance reducido a 12 municipios:** se construye V2 directamente, manteniendo la malla de 64 con `SIN_ESTACION` para los demás (así no se pierde la posibilidad de extender).
- **Solo 2019–2022 (evita la repetición de reportes):** pierde 7 años y deja 2 de 4 en régimen COVID; no se recomienda sin decisión explícita.
- **Incorporar estaciones vecinas por altitud/distancia:** requiere altitud y coordenadas de las cabeceras municipales (no disponibles en esta auditoría) y una validación por municipio con estación propia (comparar la estación vecina contra la propia).
- **Ampliar a otro departamento:** el diseño por DIVIPOLA lo permite; las tablas de referencia y los criterios de cobertura se repetirían.
