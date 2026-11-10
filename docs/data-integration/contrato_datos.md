# Contrato de datos propuesto — RESPIRA

**Estado:** contrato para futuras recepciones y procesamiento; no habilita ingesta automática.

## Alcance semántico

- Indicador SIVIGILA: conteo semanal colectivo de pacientes con IRA reportados en consulta externa para edades 0–4, construido desde IRACEXT_1 (<1), IRACEXT_2 (1 año) e IRACEXT_3 (2–4 años) sólo tras validar el diccionario del archivo/año y la regla de consolidación. No representa personas únicas, incidencia ni prevalencia.
- `COD_MUN` identifica el municipio notificador del establecimiento según el diccionario disponible; no equivale a residencia del paciente.
- `AÑO` y `SEMANA` son el período epidemiológico fuente. `FEC_NOT` se conserva como fecha de notificación y no sustituye el período.
- IDEAM: una fila diaria es observación de estación/variable. Los resúmenes semanales son derivados y deben identificar variable, unidad, cobertura, método y estación.
- DANE: población municipal proyectada anual; para este piloto se usa población del área `Total`, edad simple 0–4 sumada y sexo `Total`. No es un conteo observado semanal.

## Recepción y trazabilidad

1. Mantener el archivo recibido sin modificar y con acceso controlado; registrar nombre, tamaño, extensión, fecha/procedencia declaradas y SHA-256. Si falta hash, registrar `unknown`, no inventarlo ni atribuirlo retrospectivamente.
2. Identificar lote, versión del diccionario, año(s), hojas, delimitador/encoding cuando aplique, número de filas, columnas y fingerprint del encabezado. La misma extensión no prueba que dos libros tengan el mismo esquema.
3. Registrar fila fuente por `(lote, hoja, número de fila)`. Preservar encabezado y texto fuente para auditoría; cualquier normalización genera un derivado separado con versión de reglas.
4. No incluir datos personales identificables en tablas analíticas, logs o evidencias. Proveedor y sede son códigos institucionales restringidos al propósito de calidad/consolidación.
5. Una recarga idéntica debe ser idempotente por lote/hash; un archivo distinto crea lote nuevo. No sobrescribir silenciosamente versiones previas.

## Formatos observados y decodificación

| Fuente | Formato observado | Contrato de lectura |
|---|---|---|
| SIVIGILA | XLSX por año; la estructura/cabeceras pueden cambiar | Leer por nombre de campo y mapa versionado por libro/año; validar la hoja y encabezados antes de procesar. No mapear por posición de columna. Registrar códigos originales como texto. |
| IDEAM | `.data` delimitado por `|`, columnas `Fecha|Valor` | Validar exactamente el formato esperado, fechas y numéricos; conservar texto original. No asumir que ausencia de flag en archivo implica dato controlado o válido. |
| DANE | Libros XLSX separados por versión/periodo con diseños distintos | Aplicar mapa de encabezados específico por libro; verificar código y nombre municipal; extraer `Total` y edades simples 0–4 según documentación. No usar posiciones de columnas. |
| Productos auditados | CSV de piloto/informes | Delimitador, encoding, BOM y nombres se detectan/declaran por archivo; no inferir esquema por extensión solamente. CSV procesado no reemplaza originales. |

Se permiten nombres y etiquetas canónicas en minúscula ASCII para derivados, pero se conservan variables/códigos originales. Los códigos DIVIPOLA se serializan como cadena de cinco dígitos. El encoding y delimitador efectivos quedan registrados por lote, no asumidos globalmente.

## Validaciones bloqueantes antes de un derivado

- Esquema del año/libro coincide con un mapa revisado y versionado; columnas obligatorias presentes y no ambiguas.
- Año y semana son enteros plausibles para el evento; semanas 1–53 sólo se aceptan si existen en el calendario epidemiológico oficial correspondiente. Fechas de calendario no se deducen de `FEC_NOT`.
- `COD_MUN` se enlaza a DIVIPOLA válido sin perder ceros y con discrepancias nombre/código reportadas.
- Conteos no negativos y parseables. Nulos, texto inválido, filas repetidas y códigos desconocidos quedan en cuarentena o como issues; no se borran sin registro.
- Cada fila tiene procedencia reproducible. A falta de hash, el lote no certifica identidad exacta del archivo.
- Para clima se validan unidad, definición de variable, fecha, código de estación, rangos físicos sólo cuando exista referencia técnica documentada. La plausibilidad no modifica automáticamente el valor original.
- Para agregación semanal, generar calendario de fechas esperado por año; contar días válidos por variable. Aplicar umbral 6/7 sólo para reproducir el piloto exploratorio y etiquetarlo como regla de proyecto, no como estándar IDEAM.
- Ausencia de fila y valor cero son estados diferentes. Ninguna semana no notificada se rellena automáticamente con cero.

## Reglas de revisión obligatoria

- Filas colectivas consecutivas de una misma UPGD/sede/evento/semana (incluido el caso Chachagüí 2016 SE43 con `NUM_CON` 263/264) se conservan como `unresolved_repeat` hasta que una instrucción oficial determine reemplazo, corrección o aditividad. No crear unicidad por prestador-semana.
- Las semanas Chachagüí 2016 SE44/52 y Funes 2016 SE11/21 sin fila fuente se representan como `no_source_row`; no como cero.
- El archivo local SIVIGILA 2021 que alcanza el límite de filas de Excel no se acepta como año completo hasta contar con extracción íntegra o evidencia verificable de completitud. Una futura recepción deberá quedar como lote independiente.
- No procesar variables IDEAM `PTPM_CON_INTER`, `HR_CAL_MEDIA_D`, `TPR_CAL` o `TV_CAL` como equivalentes de las seleccionadas sin definición, unidad y validación técnica explícitas.
- Asignaciones estación-municipio permanecen candidatas hasta una evaluación documentada de representatividad.
- Cambios de versión del diccionario INS, formulario, libro DANE, catálogo IDEAM o calendario obligan a registrar una nueva versión de contrato/regla y revisar comparabilidad.

## Estados mínimos

`reported_value`, `reported_zero`, `no_source_row`, `unresolved_repeat`, `insufficient_coverage`, `pending_semantics`, `invalid`, `not_processed`. Un estado distinto de los dos primeros no debe expresarse con un valor numérico cero. Los fallos bloqueantes impiden publicar el derivado como completo; las advertencias acompañan al dato hasta resolución.
