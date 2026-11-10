# Auditoría integral de datasets RESPIRA

**Fecha de inspección:** 4 de noviembre de 2026  
**Raíz inspeccionada:** `C:\Users\MARIA VICTORIA\Desktop\universidad\SEMESTRES\QUINTO SEMESTRE\Diseño de interfaces\FINALES\RESPIRA`  
**Método:** inventario recursivo de formatos tabulares, lectura de CSV y metadatos SQLite en modo solo lectura, comparación de hashes y contraste con los informes de auditoría que ya existen en el repositorio. No se modificaron fuentes ni se ejecutaron migraciones o cargas.

## 1. Resumen ejecutivo

En el árbol físico accesible se encontraron **18 archivos con contenido tabular**: 16 CSV y 2 bases SQLite. Por similitud y propósito se identifican **7 familias de datasets/conjuntos de evidencia**: datos sintéticos de demostración; piloto analítico; inventario IDEAM histórico; cobertura IDEAM; metadatos de variables IDEAM; evidencia metodológica SIVIGILA; y artefactos de validación del piloto/calendario. No son 18 fuentes independientes.

No están físicamente presentes en la raíz inspeccionada los archivos originales IDEAM, DANE ni los libros anuales SIVIGILA 995. Tampoco está `data/processed/pilot/version_pira_2016_2022.csv`; el archivo existente se llama `piloto_respira_2016_2022.csv`. Los informes históricos describen las fuentes originales y sus resultados, pero no sustituyen los archivos de origen ni permiten repetir esta inspección de filas. El análisis de originales que sigue se marca por ello como **no verificable en el estado actual del árbol**.

El piloto semanal 2016 y 2022 es la pieza con mayor utilidad analítica: 312 filas, tres municipios y 52 semanas por municipio-año. Los informes existentes lo califican apto para exploración con limitaciones y no para entrenamiento predictivo todavía. Los datos de demostración y sus dos SQLite son sintéticos (2023–2025) y no deben confundirse con observaciones de SIVIGILA, IDEAM o DANE.

## 2. Inventario de archivos tabulares inspeccionados

La columna «faltantes» expresa celdas vacías sobre el total de celdas del CSV, calculadas sin normalizar valores semánticos. Los tipos son familias inferidas de la representación textual y no un contrato de esquema.

| Archivo | Tamaño | Registros × variables | Periodo y cobertura observados | Categoría / estado |
|---|---:|---:|---|---|
| `backend/data/simulated/ira_cases.csv` | 134,642 B | 1,560 × 11 | 2023–2025, 10 municipios de Nariño, semanas 1–52 | Sintético/exploratorio; 0% vacíos; clave municipio-año-semana única |
| `backend/data/respira.db` | 147,456 B | `ira_cases` 1,560 × 8; `municipalities` 10 × 5 | 2023–2025, Nariño simulado | SQLite de demostración; mismas cardinalidades que CSV sintético |
| `backend/tests/test.db` | 147,456 B | `ira_cases` 1,560 × 8; `municipalities` 10 × 5 | 2023–2025, Nariño simulado | Base de pruebas; mismas tablas, DDL y conteos que `respira.db` |
| `data/processed/pilot/piloto_respira_2016_2022.csv` | 97,302 B | 312 × 28 | 2016 y 2022; Chachagüí (52240), Funes (52287), Samaniego (52678); semanas 1–52 | Derivado epidemiológico + meteorológico + demográfico; 0.114% de celdas vacías |
| `data/reports/resumen_ideam_historico.csv` | 1,094 B | 5 × 13 | Cobertura temporal declarada en sus campos; resumen de variables/estaciones IDEAM | Evidencia derivada de auditoría, no observaciones crudas; 0% vacíos |
| `data/reports/resumen_ideam_narino_archivos.csv` | 70,954 B | 414 × 25 | Resumen de archivos/series IDEAM de Nariño; fechas mínima y máxima por fila | Derivado de inventario de fuentes que ahora no están en el árbol; 0.01% vacíos |
| `data/reports/cobertura_ideam_narino_estacion_anio.csv` | 317,294 B | 4,554 × 13 | Cobertura por estación-variable-año, informe declara 2012–2022 | Derivado de auditoría; 4.48% vacíos |
| `docs/data-audit/segunda-auditoria/resumen_ideam_narino_archivos.csv` | 70,954 B | 414 × 25 | Igual al resumen IDEAM anterior | Copia exacta del CSV en `data/reports` |
| `docs/data-audit/segunda-auditoria/cobertura_ideam_narino_estacion_anio.csv` | 317,294 B | 4,554 × 13 | Igual a cobertura IDEAM anterior | Copia exacta del CSV en `data/reports` |
| `reports/estaciones_candidatas_ideam.csv` | 43,945 B | 99 × 38 | Candidatas por variables y cobertura descritas para 2012–2022; Nariño | Derivado de análisis IDEAM; sin vacíos reportados |
| `reports/metadatos_variables_ideam.csv` | 2,327 B | 8 × 8 | No aplica como serie; ocho etiquetas de variable | Diccionario/evidencia de procedencia y validación, no mediciones |
| `reports/diccionario_sivigila_995.csv` | 2,894 B | 14 × 6 | No aplica como serie; campos de evento 995 | Diccionario operativo derivado; no microdatos epidemiológicos |
| `reports/cuarta_auditoria/calendario_semana_epi.csv` | 6,262 B | 104 × 9 | Semanas de 2016 y 2022; límites de calendario | Evidencia derivada del calendario; 10.897% vacíos (campos de nota opcionales) |
| `reports/cuarta_auditoria/cobertura_meteorologica.csv` | 1,638 B | 18 × 13 | 3 municipios × 3 variables × 2 años del piloto | Control de cobertura semanal; 6.41% vacíos |
| `reports/cuarta_auditoria/filas_repeticion_sivigila.csv` | 419 B | 2 × 15 | Chachagüí, 2016, semana 43 según el informe de cuarta auditoría | Evidencia reducida de repetición de reporte; no demuestra duplicación indebida |
| `reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv` | 105,150 B | 312 × 29 | Mismas claves y cobertura del piloto, 2016 y 2022 | Derivado versionado con semántica corregida; 0.111% vacíos |
| `reports/cuarta_auditoria/sha256_fuentes.csv` | 4,341 B | 26 × 5 | Snapshot de hashes; no es serie analítica | Evidencia de integridad local, con entradas cuyo baseline previo es ausente |
| `reports/cuarta_auditoria/validaciones.csv` | 8,454 B | 53 × 5 | Validaciones registradas para la cuarta auditoría | Evidencia de control; 1 fila repetida completa entre registros |

**Conteos:** 18 archivos tabulares contando los CSV de auditoría y las SQLite; 16 CSV y 2 SQLite. Los CSV de resúmenes/copias/validaciones son artefactos de auditoría, no 16 fuentes independientes. Hay además archivos JSON de configuración del frontend y archivos SQL de esquema/migración: se excluyen del conteo de datasets porque no contienen observaciones tabulares de RESPIRA. No se encontraron XLS/XLSX, JSONL, Parquet, GeoJSON, TXT de datos, ni archivos de observaciones sin extensión en el árbol inspeccionado. `backend/requirements.txt` no es un dataset.

## 3. Caracterización por dataset y familia

### A. Demostración sintética

`backend/data/simulated/ira_cases.csv` tiene 11 columnas: `municipality`, `department`, `latitude`, `longitude`, `epidemiological_week`, `year`, `cases`, `temperature`, `precipitation`, `humidity`, `data_source`. Tipos representados: texto para municipio/departamento/fuente; numérico para coordenadas, semana, año, casos y variables climáticas. Todos los 1,560 registros llevan `data_source` de datos sintéticos; están repartidos entre 10 municipios de Nariño, 2023–2025. No presenta celdas vacías ni claves municipio-año-semana repetidas. Procedencia: generación sintética del proyecto, según el propio campo fuente/ruta.

Las tablas SQLite `municipalities` (`id`, `name`, `department`, `latitude`, `longitude`) y `ira_cases` (`id`, `municipality_id`, `epidemiological_week`, `year`, `cases`, `temperature`, `precipitation`, `humidity`) contienen 10 y 1,560 filas respectivamente. Ambas bases comparten estructura y conteos. La base de tests es repetición funcional de la base de demostración; no es una fuente distinta. No se usaron hashes byte a byte para declarar que ambas bases son idénticas.

**Utilidad:** comprobar pantallas, consultas y flujo de la aplicación; no construir el dataset epidemiológico definitivo, inferir incidencia ni entrenar el modelo. Las columnas de casos y clima no acreditan relación con archivos originales. No tiene semana epidemiológica comprobada con calendario INS ni edad/grupo etario verificable. El campo `municipality` podría mapearse a DIVIPOLA solo tras agregar y validar códigos, pues el archivo no incluye código municipal.

### B. Piloto integrado

Los dos CSV de piloto tienen la misma dimensión (312 filas). El original tiene 28 variables, y la versión auditada v2 tiene 29. En ambos, la llave observada es municipio DIVIPOLA + año + semana; los informes existentes dicen que las 312 claves son únicas. Variables principales: municipio/año/semana y límites de fecha, conteo colectivo IRA reportado menor de cinco, filas de fuente y estado SIVIGILA, temperatura semanal mínima/máxima/media y días/cobertura por variable, población anual menor de cinco, estación IDEAM, archivos de origen y notas de calidad. La v2 renombra explícitamente el conteo como `ira_under5_collective_reported_patient_count` y registra el estado de consolidación.

Hay 10 celdas vacías en el CSV original y 10 en v2 según el recuento de vacíos de celdas, concentradas en el indicador IRA de cuatro municipio-semanas sin filas fuente y en valores meteorológicos de semanas bajo umbral (los informes identifican además dos semanas-variable sin seis días). Un vacío SIVIGILA significa ausencia de fila en el extracto, no cero ni ausencia de enfermedad. No se deben imputar esos valores sin resolver la causa.

Fuente declarada: SIVIGILA evento colectivo 995, IDEAM diaria y proyecciones DANE. El piloto integra 2016 y 2022 únicamente; no representa observaciones individuales, incidencia, personas únicas ni toda la población departamental. El conteo del evento 995 se describe como pacientes/atenciones colectivas reportadas por grupos menores de cinco años. La semántica y disponibilidad de campos históricos deben revisarse por versión anual. Los informes previos documentan cuatro semanas sin fila en 2016 y una repetición proveedor-semana cuyos reportes no se pudieron resolver como aditivos o correcciones.

**Utilidad:** análisis exploratorio y diseño de reglas/controles. Es el único conjunto integrado localizado. No es todavía suficiente para entrenamiento predictivo defendible por la escasa selección (3 municipios, 2 años), semanas ausentes, repetición no resuelta, semántica colectiva y limitaciones de verificación de fuente.

### C. Evidencia IDEAM histórica

`resumen_ideam_narino_archivos.csv` caracteriza 414 filas/series y 25 columnas, entre ellas código de estación, municipio, etiqueta de variable, número de registros, fechas mínima/máxima, frecuencia observada, fechas nulas, valores no numéricos, repeticiones, desorden, ceros, negativos y alertas extremas. `cobertura_ideam_narino_estacion_anio.csv` ofrece 4,554 combinaciones estación-municipio-variable-año con registros, días válidos/esperados, completitud y extremos. Las dos copias de estos archivos en `docs/data-audit/segunda-auditoria/` tienen los mismos SHA-256 de sus copias en `data/reports`, por tanto son duplicados binarios deliberados de evidencia preservada.

`resumen_ideam_historico.csv` resume cinco variables/estaciones. `estaciones_candidatas_ideam.csv` lista 99 candidatas con código, coordenadas, categoría/estado de catálogo y resumen de cobertura 2012–2022. Estos resúmenes permiten rastrear criterios y orientar recuperación de fuentes, pero no sustituyen los archivos meteorológicos diarios ni prueban observaciones específicas sin acceso a estos. El informe anterior señala que las candidatas no equivalen a estaciones certificadas ni a continuidad histórica.

`metadatos_variables_ideam.csv` contiene 8 etiquetas: `PTPM_CON_INTER`, `HR_CAL_MEDIA_D`, `TPR_CAL`, `TV_CAL`, `TSSM_MN_D`, `TSSM_MX_D`, `TSSM_MEDIA_D` y `TSSM_CON`. El informe ya existente establece que equivalencia/unidad de precipitación y varias etiquetas de humedad/punto de rocío/tensión de vapor requieren confirmación; el piloto usa variables de temperatura documentadas, pero la calidad por observación no está demostrada con flags locales.

**Relación con SIVIGILA:** posible agregación estación/municipio + año + semana, o más apropiadamente por fecha diaria agregada con calendario epidemiológico validado. El código de estación enlaza catálogo con observaciones IDEAM, no directamente con SIVIGILA. El cruce municipio debe respetar DIVIPOLA/código, alias, representatividad espacial y estación asignada. Los CSV actuales son resúmenes, así que no es posible recalcular datos meteorológicos desde observaciones crudas en esta auditoría.

### D. Evidencia SIVIGILA

`diccionario_sivigila_995.csv` registra 14 campos con significado operativo, dominio/unidad, reglas y cautelas. `filas_repeticion_sivigila.csv` conserva dos registros con campos analíticos limitados y sin identificadores personales descriptivos; facilita revisar la repetición reportada. No son microdatos del evento. Las auditorías Markdown existentes resumen la estructura de los libros 995 de 2012–2022, pero en el estado actual no se halló ninguno de esos libros. En consecuencia, cantidad de filas, columnas, hojas, faltantes y duplicados de cada XLSX anual no pueden recontarse ahora.

**Utilidad:** el diccionario puede guiar una integración futura cuando se recuperen libros y versiones de diccionario anual; los dos registros reducidos permiten examinar un caso de repetición ya encontrado. Cruce futuro por código DIVIPOLA (`cod_mun`), año y semana epidemiológica, después de validar calendarios, códigos y versiones. Edad se expresa en grupos/campos del evento colectivo, no necesariamente como edad individual.

### E. Calendario y controles del piloto

`calendario_semana_epi.csv` compara los límites derivados del calendario INS con los límites actuales del piloto para 104 semanas de 2016 y 2022. `cobertura_meteorologica.csv` resume 18 series estación-variable-año, fechas diarias válidas, semanas que cumplen umbral, errores de parseo y fechas duplicadas. `validaciones.csv` registra 53 controles; el informe de cuarta auditoría reporta 47 PASS, 0 FAIL y 6 WARNING/PENDING. `sha256_fuentes.csv` guarda hashes y baseline-status: un snapshot local no autentica por sí mismo una descarga oficial. Estos archivos son evidencia/metadatos y no predictores nuevos.

## 4. Archivos buscados que no están disponibles

La búsqueda recursiva por nombre y extensión confirmó **0 coincidencias físicas** para:

- `Cat_logo_Nacional_de_Estaciones_del_IDEAM (1).csv`
- `NARI_O.csv`
- `Datos_de_Estaciones_de_IDEAM_y_de_Terceros.csv`
- `PPED-AreaSexoEdadNac-2018-2070.xlsx`
- `version_pira_2016_2022.csv`
- Libros SIVIGILA evento 995 2012–2022 (incluidos `Datos_2012_995.xlsx` y `Datos_2021_995.xlsx`)

Se encontró `data/processed/pilot/piloto_respira_2016_2022.csv`, no `version_pira_2016_2022.csv`. Un informe de 25 de octubre de 2026 (`data/reports/INFORME_AUDITORIA_DATASETS_RESPIRA_20261025.md`) afirma que inspeccionó catálogos IDEAM, observaciones de 156,311 filas, libro DANE nacional y libros SIVIGILA 2012–2022. Ese documento es evidencia histórica de disponibilidad al momento de aquella auditoría, pero esos binarios no estaban en el árbol el 4 de noviembre. La procedencia y sus dimensiones aquí solo se pueden citar como **declaradas por la auditoría previa**, no como verificación actual. Los datos locales están ignorados/no versionados según `data/README.md`; podrían residir fuera de esta copia del proyecto.

## 5. Matriz principal de compatibilidad y utilidad

| Dataset | Fuente | Periodo | Cobertura | Registros | Variables | Categoría | Utilidad | Limitaciones | Estado |
|---|---|---|---|---:|---:|---|---|---|---|
| IRA sintético CSV + SQLite | Generación de prueba local | 2023–2025 | 10 municipios de Nariño | 1,560 hechos; 10 municipios | Casos, semana/año, clima, coordenadas | Sintético/exploratorio | Validar software/demos; no modelar epidemiología real | Sin fuente observacional, DIVIPOLA, edad ni vínculo con INS/IDEAM | Presente; excluir de análisis epidemiológico |
| Piloto RESPIRA | INS/SIVIGILA + IDEAM + DANE declarados | 2016 y 2022 | Chachagüí, Funes, Samaniego | 312 semanas | IRA colectiva, temperatura, población, estado/cobertura | Derivado/integrado | Exploración temporal y pruebas de integración | Cuatro semanas sin fila; dos semanas-variable bajo umbral; repetición sin resolver; solo 3 municipios × 2 años | Presente; exploratorio, no entrenamiento |
| Resumen/cobertura IDEAM | IDEAM indirecto; generado por auditoría local | Declara 2012–2022 | Estaciones/series de Nariño | 414 filas de series; 4,554 estación-variable-año | Fechas, frecuencias, conteos, completitud, métricas QC | Meteorológico derivado | Selección de fuentes y diseño de controles | Observaciones originales no presentes; códigos/etiquetas no verificables contra crudo | Presente; evidencia secundaria |
| Estaciones candidatas IDEAM | IDEAM indirecto; derivado de catálogo/series | Declara 2012–2022 | Nariño | 99 estaciones | Código, localización, estado, variables y cobertura | Geográfico + meteorológico derivado | Guiar solicitud/selección de series | No acredita disponibilidad histórica ni representatividad espacial | Presente; candidatas |
| Metadatos variables IDEAM | IDEAM/documentación citada por auditoría | No aplica | Variables del piloto | 8 definiciones | Etiqueta, interpretación, unidad, uso y estado | Complementario | Resolver significado y restricciones de variables | Confirma pendientes; varias etiquetas no están validadas | Presente; requiere confirmación de fuente |
| Diccionario SIVIGILA 995 y caso repetido | INS + análisis local | Marco 2012–2022; repetición 2016 | Evento 995; caso de Chachagüí | 14 campos de diccionario; 2 filas de evidencia | Semana, municipio, campos agregados IRA y reporte | Epidemiológico derivado | Guiar mapeo y conciliación de anomalía | Libros anuales ausentes; no permite recalcular métricas de la serie | Presente; apoyo, no fuente primaria |
| Calendario y QC piloto | INS citado + controles locales | 2016/2022 | Piloto | 104 semanas; 18 series; 53 checks | Fechas, cobertura, duplicados, estado de validación | Complementario/derivado | Reproducibilidad y trazabilidad | Reglas limitadas a dos años y piloto; algunas advertencias siguen pendientes | Presente; evidencia auditable |

### Compatibilidad de llaves

| Pareja | Llave candidata | Compatibilidad observada | Pendientes antes de combinar |
|---|---|---|---|
| SIVIGILA ↔ piloto | DIVIPOLA municipio + año + semana | Integrada en el piloto en 3 municipios y 2 años; claves del piloto únicas según validación existente | Recuperar libros originales, validar esquema anual/calendario; resolver vacíos y repetición; evitar tratar ausencia como cero |
| IDEAM observación ↔ estación | Código de estación + fecha + variable/sensor | Esquema de la extracción diaria descrito en informes anteriores; hoy no está el crudo | Recuperar series, diccionario, unidades, flags, frecuencia y estado aprobado/preliminar |
| IDEAM ↔ SIVIGILA/piloto | Municipio/DIVIPOLA + fecha, agregada a semana | El piloto enlaza estaciones con municipios seleccionados | Verificar estación-municipio por código, asignación espacial y semanas; no basta nombre municipal |
| DANE ↔ SIVIGILA | DIVIPOLA + año + edad/grupo etario | En piloto hay una población anual menor de cinco años atribuida a fuente DANE | Recuperar anexo municipal y validar territorio, área Total, edades simples 0–4 y sexo sin doble suma |
| Sintético ↔ fuente real | Nombre de municipio + semana/año | Solo coincidencia textual/geográfica posible | No hay ID ni evidencia de que casos/clima sintéticos correspondan a fuente real; no unir para inferencia |

## 6. Duplicados, derivados y calidad

- Las copias de `resumen_ideam_narino_archivos.csv` y `cobertura_ideam_narino_estacion_anio.csv` en `docs/data-audit/segunda-auditoria/` son idénticas por SHA-256 a sus equivalentes en `data/reports/`.
- `reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv` es derivado/versionado del piloto original con 29 frente a 28 columnas y etiqueta/reclasificación metodológica del conteo/repetición. No reemplaza el original.
- La base de pruebas y la base de demostración comparten DDL, conteos y esquema; son artefactos de desarrollo con contenido sintético, no fuentes independientes.
- En el piloto original hay 312 claves y cero filas repetidas exactas según el conteo; 10 celdas vacías. Los informes existentes registran cuatro semanas sin fila SIVIGILA (Chachagüí SE44/52 y Funes SE11/21 de 2016), más una repetición proveedor-semana en Chachagüí SE43 que no se puede declarar duplicado o doble conteo confirmado.
- En las validaciones existentes, 2021 SIVIGILA alcanza el límite de filas de Excel. La auditoría previa lo considera de integridad no demostrada. Como su XLSX no está aquí, esta inspección no puede recuperar ni verificar esa integridad.
- Archivos IDEAM crudos, DANE y SIVIGILA no disponibles: faltantes, tipos, dimensiones y duplicados propios de esos originales quedan **sin auditoría actual**. Los resúmenes secundarios no resuelven estos controles.
- Los nombres de columnas con caracteres acentuados se muestran mojibake al decodificarse como UTF-8 en dos CSV de resúmenes (`A�o`, `EsNari�o`), lo que indica posible codificación distinta o datos ya mal codificados. Confirmar encoding antes de automatizar ingesta.
- La inferencia de tipos del CSV es superficial; DIVIPOLA/códigos de estación deben tratarse como cadenas para preservar ceros iniciales (aunque los códigos vistos no necesariamente comiencen con cero).

## 7. Procedencia que requiere confirmación

1. **Fuentes IDEAM originales:** confirmar descarga, extracción y corte temporal, propietarios de datos, códigos de estación/sensor, unidades, equivalencia de etiquetas y banderas/estado de calidad. Los nombres/medidas de archivos no existen localmente para cotejo.
2. **Datos DANE:** recuperar el XLSX municipal adecuado. El informe anterior describe un libro nacional por área/sexo/edad que no aporta desagregación municipal; no usarlo para población 0–4 de cada municipio de Nariño.
3. **SIVIGILA:** recuperar libros 995 anuales, metadatos del lote y diccionario por versión/año. Confirmar completitud 2021 y explicar semanas sin fila, reportes sucesivos y cambios de columnas.
4. **Sintético:** mantener marca sintética visible en toda exportación/entorno de demostración; no atribuirlo a INS.
5. **Derivados:** preservar vínculo reproducible desde cada variable piloto al archivo/hoja/rango/fila fuente, especialmente si se vuelve a generar desde los originales.

## 8. Recomendaciones para el dataset definitivo

1. Recuperar en un directorio de solo lectura los originales fuente y generar manifiesto con nombre, proveedor, fecha de descarga, versión, hash SHA-256, tamaño, hojas/filas y licencia/restricción de acceso.
2. Auditar los XLSX anuales de SIVIGILA individualmente; conservar sus originales intactos y construir un diccionario versionado por año. Validar DIVIPOLA y calendario INS anual antes de agregar por semana.
3. Conseguir población DANE municipal por edad simple para territorio/periodo correctos. No derivar población municipal de la hoja nacional agregada.
4. Obtener series IDEAM históricas crudas; enlazar por código exacto estación y variable, validar cobertura y flags, y documentar reglas de agregación diaria-semanal y zona horaria.
5. Mantener ausencias como NA con motivo explícito hasta confirmar si significan no notificación, registro no entregado o cero real. Resolver reportes repetidos con regla del proveedor y evidencia institucional.
6. Separar claramente tabla de fuente original, tablas derivadas y datos sintéticos de prueba. Incluir `source_file`, hash, fecha/versión, regla de transformación y nivel de calidad por fila/campo.
7. Ampliar validación a más años y municipios y revisar estabilidad de esquemas, sesgo de cobertura y disponibilidad de predictores antes de evaluar entrenamiento. No usar estos datos para estimar causalidad o incidencia individual.

## 9. Alcance y límites

Esta auditoría caracteriza el contenido presente y la evidencia documental existente; no elimina ni transforma fuentes, no ejecuta cargas, no accede a PostgreSQL/Supabase ni afirma integridad de archivos ausentes. Los resúmenes históricos pueden reflejar una instantánea distinta a la inspeccionada. Para cerrar la auditoría de originales se requieren los binarios no presentes y sus metadatos de procedencia. Este informe no recomienda descartar fuentes ni cerrar el alcance funcional de RESPIRA.

## Anexo A. Esquemas observados

Los encabezados de abajo se transcriben del archivo localizado. Tipos inferidos: numérico cuando todos los valores no vacíos se representaron como números; texto/mixto para fechas, etiquetas, identificadores y valores heterogéneos. En tablas SQLite, los tipos son los declarados en el DDL.

| Archivo | Columnas (orden del archivo) | Tipos inferidos |
|---|---|---|
| `backend/data/simulated/ira_cases.csv` | `municipality, department, latitude, longitude, epidemiological_week, year, cases, temperature, precipitation, humidity, data_source` | texto, texto, numérico ×8, texto |
| `data/processed/pilot/piloto_respira_2016_2022.csv` | `municipality_divipola, municipality_name, year, epi_week, epi_week_start, epi_week_end, ira_under5_reported_consultations, sivigila_source_rows, sivigila_duplicate_provider_week_keys, sivigila_week_status, temp_min_weekly, temp_min_days_observed, temp_min_coverage_pct, temp_max_weekly, temp_max_days_observed, temp_max_coverage_pct, temp_mean_weekly, temp_mean_days_observed, temp_mean_coverage_pct, population_under5_annual, ideam_station_code, ideam_station_name, source_dane, source_ideam_tmin, source_ideam_tmax, source_ideam_tmean, source_sivigila_file, quality_notes` | numérico, texto, numérico ×2, texto ×2, numérico ×3, texto, numérico ×9, texto, numérico, texto ×7 |
| `data/reports/resumen_ideam_historico.csv` | `CodigoEstacion, Variable, Parametro, Unidad, FechaMin, FechaMax, Registros, AniosDisponibles, FrecuenciaEstimada, NivelAprobacionPrincipal, EsNariño, Municipio, Departamento` | numérico ×1; restantes texto/mixto salvo `Registros` numérico |
| `data/reports/resumen_ideam_narino_archivos.csv` y copia en `docs/data-audit/segunda-auditoria/` | `Carpeta, CodigoEstacion, CodigoEnNombre, Etiqueta, Municipio, Departamento, CategoriaCatalogo, EstadoCatalogo, Registros, FechaMin, FechaMax, FrecuenciaObservada, IntervaloMedianoHoras, MarcasPorDiaMediana, NulosFecha, ValoresVacios, ValoresNoNumericos, DuplicadosExactos, MarcasFechaHoraDuplicadas, FueraDeOrden, Ceros, Negativos, PrecipSobre135mm, TempMenorMenos20, TempMayor60` | Texto/mixto en etiquetas/ruta/fechas/frecuencia; numérico en códigos, registros, métricas y contadores |
| `data/reports/cobertura_ideam_narino_estacion_anio.csv` y copia en `docs/data-audit/segunda-auditoria/` | `CodigoEstacion, Municipio, VariableID, Año, Filas, ValoresValidos, DiasConValor, DiasEsperados, CompletitudPct, Ceros, Negativos, Min, Max` | texto/mixto en municipio/variable; numérico en código, año y métricas; encoding de `Año` requiere confirmación |
| `reports/estaciones_candidatas_ideam.csv` | `codigo_estacion, nombre_estacion, municipio, departamento, latitud, longitud, altitud, tecnologia, categoria, estado_catalogo, precipitacion_disponible, temperatura_min_disponible, temperatura_max_disponible, temperatura_media_disponible, cobertura_precipitacion_2012_2022, cobertura_temp_min_2012_2022, cobertura_temp_max_2012_2022, cobertura_temp_media_2012_2022, variables_conjuntas, estado, justificacion, dias_validos_prec_2012_2022, dias_faltantes_prec_2012_2022, mayor_hueco_prec_dias, dias_validos_tmin_2012_2022, dias_faltantes_tmin_2012_2022, mayor_hueco_tmin_dias, dias_validos_tmax_2012_2022, dias_faltantes_tmax_2012_2022, mayor_hueco_tmax_dias, dias_validos_tmedia_2012_2022, dias_faltantes_tmedia_2012_2022, mayor_hueco_tmedia_dias, anios_ge80_prec, anios_ge80_tmin, anios_ge80_tmax, anios_ge80_tmedia, catalogo_coincide_por_codigo` | numérico en código/coordenadas/altitud/coberturas/contadores; resto texto/mixto (incluye indicadores) |
| `reports/metadatos_variables_ideam.csv` | `etiqueta_local, interpretacion_candidata, unidad, periodicidad, documento_oficial, estado_validacion, uso_en_piloto, observaciones` | texto |
| `reports/diccionario_sivigila_995.csv` | `campo_local, significado_operativo, dominio_o_unidad, regla_aplicada, limite_o_cautela, fuente` | texto |
| `reports/cuarta_auditoria/calendario_semana_epi.csv` | `year, epi_week, derived_INS_calendar_start, derived_INS_calendar_end, current_pilot_start, current_pilot_end, start_difference_days, end_difference_days, boundary_note` | numérico en año, semana y diferencias; fechas/notas texto |
| `reports/cuarta_auditoria/cobertura_meteorologica.csv` | `municipality_divipola, municipality_name, station_code, variable, year, daily_valid_dates, duplicate_date_extras, parse_errors_all_file_periods, weeks_with_6plus_days, weeks_below_6_days, weeks_below_6_list, first_daily_date, last_daily_date` | numérico en códigos, año y conteos; resto texto/mixto |
| `reports/cuarta_auditoria/filas_repeticion_sivigila.csv` | `municipality_divipola, municipality_name, year, epi_week, provider_code, provider_subindex, num_con, source_excel_row, IRACEXT_1, IRACEXT_2, IRACEXT_3, row_indicator_sum, same_full_source_row_as_other_in_group, same_provider_week_group_n, num_con_unique_within_group` | numérico en año, semana, códigos/contadores; municipio y flags texto |
| `reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv` | `municipality_divipola, municipality_name, year, epi_week, epi_week_start, epi_week_end, sivigila_source_rows, sivigila_week_status, temp_min_weekly, temp_min_days_observed, temp_min_coverage_pct, temp_max_weekly, temp_max_days_observed, temp_max_coverage_pct, temp_mean_weekly, temp_mean_days_observed, temp_mean_coverage_pct, population_under5_annual, ideam_station_code, ideam_station_name, source_dane, source_ideam_tmin, source_ideam_tmax, source_ideam_tmean, source_sivigila_file, quality_notes, ira_under5_collective_reported_patient_count, sivigila_repeated_provider_week_groups, sivigila_consolidation_status` | numérico en códigos/año/semana/mediciones/contadores; resto texto/mixto |
| `reports/cuarta_auditoria/sha256_fuentes.csv` | `file, bytes, sha256, baseline_status, prior_sha256` | texto salvo `bytes` numérico |
| `reports/cuarta_auditoria/validaciones.csv` | `status, id, area, result, evidence` | texto |

Tablas SQLite: `municipalities(id INTEGER, name VARCHAR(100), department VARCHAR(100), latitude FLOAT, longitude FLOAT)`; `ira_cases(id INTEGER, municipality_id INTEGER, epidemiological_week INTEGER, year INTEGER, cases INTEGER, temperature FLOAT, precipitation FLOAT, humidity FLOAT)`. Claves/relaciones según DDL: ambas tienen `id` como PK y `ira_cases.municipality_id` referencia `municipalities.id`.
