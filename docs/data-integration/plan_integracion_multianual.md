# Plan de integración multianual — RESPIRA

**Estado:** secuencia propuesta. No ejecuta importaciones ni fija calendario de entrega.

## Etapa 0 — Gobierno y alcance (bloqueante)

- Confirmar responsable funcional, finalidad del indicador y población objetivo; resolver si RESPIRA mostrará únicamente conteos notificados o un indicador distinto.
- Obtener versiones oficiales de diccionario/formulario por cada año, reglas de ajuste de reportes y permisos de uso/retención.
- Acordar manifiesto de recepción, preservación de archivos originales, roles de acceso y política de no incorporar datos personales.
- Aprobar si los resultados exploratorios pueden mostrarse fuera de un entorno interno y bajo qué advertencias.

**Salida:** contrato aprobado y fuentes/versiones identificables. Sin esto no se declara serie multianual integrada.

## Etapa 1 — Resolver estructura e integridad SIVIGILA

1. Conseguir una versión completa verificable de 2021 o marcar ese año como no disponible; comparar conteos/hashes de futuras extracciones.
2. Obtener diccionarios por año, en particular 2022, y confirmar semántica/ámbito de IRACEXT_1–3.
3. Solicitar regla oficial para `NUM_CON` y reportes repetidos; conservar filas originales mientras se resuelve.
4. Incorporar calendario epidemiológico completo por año, incluido SE53 donde corresponda, con fechas y referencia documental.
5. Construir matriz municipio-año-semana con estados de reporte explícitos; distinguir cero, no notificación, faltante del extracto e inválido.

**Salida:** lotes SIVIGILA trazables, completitud conocida, derivado semanal reproducible y issues pendientes visibles.

## Etapa 2 — Semántica y representatividad meteorológica

- Confirmar catálogo, códigos, metadatos y cambios de estación; cotejar período de operación y calidad.
- Consultar IDEAM sobre significado/unidad de variables candidatas y obtener flags/registros de control si existen.
- Resolver estaciones representativas por municipio, considerando ubicación, elevación y cobertura espacial; conservar estado candidato mientras se evalúa.
- Documentar calendarios y cobertura diaria; cuantificar faltantes, extremos, cambios de instrumento/estación y quiebres temporales.
- Reproducir variables/umbrales del piloto con código versionado; para cada variable y semana conservar días esperados/válidos y lineage. No completar faltantes ni convertir unidad sin regla aprobada.

**Salida:** series climáticas con significado conocido y limitaciones espaciales/temporales cuantificadas.

## Etapa 3 — Integración DANE anual

- Mantener mapas de encabezado independientes por libro/versión (2005–17, 2018–42 u otra versión aplicable).
- Verificar DIVIPOLA, nombre, departamento, área, edades simples, sexo y año de referencia.
- Revisar continuidad y revisiones entre versiones; conservar valor publicado y versión, sin mezclarlas silenciosamente.
- Asociar el dato anual al indicador sólo después de aprobar finalidad, denominador y método. No generar una tasa automática a partir del conteo exploratorio.

**Salida:** panel municipal anual versionado y reconciliado, con sus revisiones documentadas.

## Etapa 4 — Ensamble analítico y controles

- Unir por DIVIPOLA + año/semana oficial, asignación de estación vigente y regla de agregación aprobada.
- Evitar interpolar o imputar por defecto. Si se propone imputación para análisis, mantener valor observado separado del imputado y evaluar sensibilidad.
- Validar integridad referencial, duplicados por identidad de fuente, calendario, cobertura y unidades.
- Producir reporte de cobertura/ausencia, perfil de calidad, lineage por indicador y manifiesto de hashes.
- Comparar resultados con extractos independientes y revisión epidemiológica/climatológica antes de uso operativo.

**Salida:** conjunto analítico versionado, con reglas, limitaciones y ruta de auditoría completa.

## Etapa 5 — Decisión de persistencia en PostgreSQL

Una vez aprobados gobierno, contrato y arquitectura, diseñar migraciones reversibles, respaldos/recuperación, permisos mínimos, cifrado/secretos fuera del repositorio, retención, monitoreo y operación. Ensayar en entorno aislado con datos sintéticos; definir convivencia con SQLite y estrategia de despliegue antes de apuntar la aplicación. La propuesta SQL de este paquete es sólo un artefacto de revisión: no habilita ni ejecuta conexión.

## Etapa 6 — Puerta independiente para modelado predictivo

Sólo considerar modelado cuando la definición del objetivo sea epidemiológicamente válida; haya cobertura y comparabilidad multianual suficientes; el indicador no dependa de duplicados o extracción incompleta; y exista evaluación temporal/espacial, prevención de fuga de datos, incertidumbre, revisión profesional, monitoreo de deriva y proceso de retiro. El conjunto del piloto actual no satisface por sí solo esta puerta y la aplicación usa reglas determinísticas; no hay IA activa en esta fase.

## Orden sugerido para iniciar

1. Resolver los bloqueos SIVIGILA 2021, diccionario 2022, reportes consecutivos y calendario oficial por año.
2. Solicitar evidencia IDEAM de variables/QC y revisar estaciones.
3. Acordar metodología epidemiológica y reglas de faltantes.
4. Aprobar modelo de persistencia y contrato; luego implementar en una fase separada.
5. Extender municipios/años por lotes, exigiendo aceptación de calidad para cada lote.
