# Criterios de aceptación — integración RESPIRA

**Estado actual:** especificación de aceptación futura. El piloto auditado conserva utilidad exploratoria, pero no equivale a serie multianual productiva ni a conjunto listo para predicción.

## Nivel 1 — Integridad y trazabilidad del lote

Un lote puede aceptarse técnicamente cuando:

- Archivo original preservado, lote/versiones identificados y hash registrado (o explícitamente desconocido).
- Conteo de filas/hojas/columnas y fingerprint de esquema documentados; mapa por versión aplicado y revisado.
- Cada registro derivado remite a lote y fila fuente; las reglas/código/insumos de transformación son reproducibles.
- Calendario por año está documentado; semanas 1–53 se tratan con fuente oficial específica.
- Claves DIVIPOLA son válidas y las discrepancias nombre/código quedan resueltas o bloquean los registros afectados.
- Nulos, ausencia de fila, cero, duplicados y valores inválidos mantienen estados distinguibles.
- No se introdujeron identificadores personales en el conjunto analítico/logs.

## Nivel 2 — Aceptación semántica y comparabilidad

Se requiere además:

- Definición, unidad, universo y método del indicador aprobados por responsable epidemiológico para cada versión de fuente.
- Regla de repetición/corrección SIVIGILA formalmente definida antes de consolidar reportes múltiples.
- Completitud de cada extracto demostrada; los años conocidos como limitados no se marcan completos.
- Variables climáticas y unidades verificadas; estado de calidad documentado; representatividad estación-municipio evaluada.
- Cobertura diaria/semanal y faltantes expuestos por variable, municipio, estación y año; regla de agregado reproducible y versionada.
- Población DANE proviene de versión y área explícitas y se usa sólo para un denominador/metodología aprobados.
- Revisión independiente de muestras fuente y resultados, con resolución de issues bloqueantes.

No se fija un umbral estadístico universal en esta especificación. El umbral exploratorio de 6/7 días sólo reproduce el piloto auditado; cualquier otro uso requiere justificación técnica aprobada.

## Nivel 3 — Aceptación para uso operativo o predictivo

Además del nivel 2: definición de objetivo y horizonte; tamaño/cobertura representativos; validación temporal y espacial sin fuga; comparación con línea base; métricas y umbrales acordados por responsables; calibración/incertidumbre; análisis de sesgo y sensibilidad a faltantes/cambios de vigilancia; revisión humana; monitoreo de deriva y mecanismo de desactivación. La aprobación técnica no constituye autorización clínica ni reemplaza criterio profesional.

## Estado del material actual

| Componente | Nivel 1 | Nivel 2 | Nivel 3 | Estado/limitación |
|---|---|---|---|---|
| Tres artefactos preservados de segunda auditoría | Cumple según hashes previamente cotejados | No aplica por sí solo | No | Reproducibilidad de artefactos, no certificación de fuente original. |
| Piloto SIVIGILA 2016/2022, 3 municipios | Parcial: trazabilidad y hallazgos auditados; conservar caveats | No: `NUM_CON`, 2022 local dictionary, ausencias y 2021 pendientes | No | Conteo colectivo reportado exploratorio, no personas/incidencia. |
| Clima IDEAM del piloto | Parcial: parsing/reglas reproducibles y cobertura calculada | No: QC/semántica de candidatos y representatividad pendientes; valores semanales faltantes | No | Candidatos observacionales de estaciones puntuales. |
| Población DANE auditada | Parcial: mapas por libro y seis valores del piloto identificados | Parcial: versión/anualidad conocidas, falta decisión de denominador | No | No convertir automáticamente a tasa semanal. |
| Aplicación existente | Adecuada para demo local con semilla sintética etiquetada | No para fuentes oficiales/missingness/provenance | No | API/modelos requieren cambios separados para datos reales. |

## Decisión de publicación

Un lote Nivel 1 puede usarse para análisis técnico interno con advertencias visibles si los bloqueos están identificados. Sólo Nivel 2 habilita una serie integrada comparable para el propósito aprobado. Nivel 3 exige revisión separada del uso predictivo. No declarar el piloto “listo para IA” ni ocultar estados incompletos para satisfacer un criterio numérico.
