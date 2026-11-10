# Diseño de integración de datos RESPIRA

**Versión documental:** 0.2.0-draft · **Estado:** diseño original (Fase 5) + implementación parcial local de la Fase 2.2.

Esta carpeta especifica cómo preparar, trazar y validar importaciones de SIVIGILA, IDEAM y DANE. La Fase 2.2 implementó el subconjunto descrito en [Implementación Fase 2.2](#implementación-fase-22); `postgresql_schema_proposal.sql` queda como referencia de diseño (esquema `respira_data`), superada para las tablas implementadas por la migración `0003` en `public`. No se ha importado ningún dato oficial ni se integra IA.

## Documentos

- [Diagnóstico de arquitectura y puntos de integración](diagnostico_arquitectura.md)
- [Diccionario de datos versionado](diccionario_datos_respira.md)
- [Modelo lógico y relaciones](modelo_datos.md)
- [Propuesta SQL PostgreSQL](postgresql_schema_proposal.sql)
- [Contrato de importación](contrato_datos.md)
- [Plan multianual](plan_integracion_multianual.md)
- [Criterios de aceptación](criterios_aceptacion.md)

Las limitaciones y cierres requeridos permanecen en el [registro de decisiones pendientes](../../reports/decisiones_pendientes_datos.md). La evidencia de la cuarta auditoría está en [cuarta_auditoria_respira.md](../../reports/cuarta_auditoria_respira.md) y sus resultados automáticos en `reports/cuarta_auditoria/`.

## Implementación Fase 2.2

Código: `backend/app/models/integration.py` (modelos), `backend/migrations/versions/0003_capa_de_integracion_de_datos.py` (migración), `backend/app/importers/` (lectores, validadores, cargador) y `backend/scripts/validate_source.py` (validación sin base de datos). SQL de 0003 para revisión (incluye 7 `ALTER` sobre `municipalities`): [migracion_0003.sql](migracion_0003.sql).

**Tablas nuevas (esquema `public`).** Cambios sobre `municipalities` (compatibles, sin pérdida de datos): columna opcional `divipola_code` (única, 5 dígitos) y coordenadas opcionales (ambas o ninguna). `ira_cases` y `users` no se tocan. La API y el mapa actuales solo exponen municipios con coordenadas (`MunicipalityRepository`), de modo que un municipio del catálogo oficial sin coordenadas verificadas no rompe la app.

| Tabla | Propósito |
|---|---|
| `data_source` | Fuente institucional (`sivigila_995`, `ideam`, `dane`). |
| `import_batch` | Una recepción de archivo: nombre, SHA-256 (único por fuente → recarga idempotente), versión de la fuente, huella de esquema, `transformation_version`, filas leídas, completitud (`unknown` … `known_limited`) y estado de validación. |
| `weather_station` | Catálogo IDEAM (código único). No se asigna a municipios: la representatividad sigue pendiente (D-03). |
| `sivigila_report` | Una fila fuente = un reporte colectivo (hoja + fila de origen únicas por lote). Conserva `NUM_CON`, prestador/sede y los tres IRACEXT. **Sin UNIQUE por prestador-semana** (D-01); las repeticiones se marcan `unresolved_repeat`. |
| `climate_observation` | Observación diaria estación-variable-fecha con texto y unidad originales. Faltante = `NULL` + estado `missing`. |
| `annual_population` | Proyección DANE anual por municipio/área/edad/sexo; no se replica por semana. |
| `data_quality_issue` | Cada rechazo o advertencia, con lote, hoja/fila, código, severidad y estado. |

**Relaciones:** `data_source 1─N import_batch 1─N {sivigila_report, climate_observation, annual_population, data_quality_issue}`; `weather_station 1─N climate_observation`; `import_batch 1─N weather_station` (catálogo). `municipality_id` es una FK **opcional** a `municipalities`: el código DIVIPOLA de la fuente se guarda siempre en `municipality_code` (texto de 5 dígitos) y el enlace se resuelve por `municipalities.divipola_code`, que identifica al municipio oficial. Decisión confirmada: DIVIPOLA es el identificador; las coordenadas solo se cargan cuando estén verificadas (nunca aproximadas).

**Existencia del municipio vs. disponibilidad geográfica.** Un municipio *existe* en el catálogo por su DIVIPOLA (`divipola_code`, opcional durante la transición desde los registros sintéticos); sus coordenadas son opcionales y solo se cargan si están verificadas (nunca aproximadas ni copiadas de otro municipio). Un municipio sin coordenadas puede existir y recibir datos de integración, pero **no está disponible para funcionalidades geográficas**: el mapa y los listados de la API actual consumen únicamente municipios con coordenadas (`MunicipalityRepository`). Cuando el contrato de la API admita ubicaciones ausentes, esta restricción se podrá retirar.

**Cadena de migraciones.** `0001 → 0002 → 0003` es lineal (un solo head, comprobado por prueba). El `upgrade` de 0003 no modifica ni elimina filas existentes, no importa datos y no elimina tablas; sus `ALTER` sobre `municipalities` solo agregan una columna opcional y relajan `NOT NULL`. Sus restricciones están cubiertas por `tests/test_postgres_schema.py`. El `downgrade` es destructivo únicamente respecto de lo que introduce 0003 (las siete tablas y `divipola_code`) y no debe ejecutarse sobre una base con datos reales sin evaluación previa; falla sin borrar nada si hay municipios sin coordenadas.

**Diferencias respecto a la propuesta original:** esquema `public` en lugar de `respira_data`; PK `id`; un único `validation_status` (`valid`, `pending`, `rejected`, `missing`, `derived`) reemplaza a `quality_status`; `municipalities` (existente) con `divipola_code` en lugar de una tabla `municipality` nueva; sin `epidemiological_week`, `station_assignment`, `processing_run*`, `weekly_ira_indicator`, `station_weekly_summary` ni tablas de linaje (dependen de D-01, D-02, D-11 y D-15). `derived` está reservado para esa capa futura y las tablas fuente no lo usan. El registro D-14 de `reports/decisiones_pendientes_datos.md` (SQLite por defecto) quedó desactualizado desde la Fase 1 y se conserva sin editar por ser parte de la auditoría.

**Estados de validación:** `valid` = pasó todas las reglas estructurales (no certifica semántica epidemiológica); `pending` = utilizable pero con reservas (semana 53 sin calendario, variable IDEAM sin semántica confirmada, conteos parciales, fecha repetida, estación aún no cargada); `rejected` = viola una regla bloqueante (se conserva con su hallazgo); `missing` = la fuente no trae el valor (NULL, nunca 0).

**Reglas de validación (`app/importers`):**

- SIVIGILA: evento 995; DIVIPOLA de 5 dígitos (y existente si se aporta catálogo); año 2000–2100; semana 1–53 (53 = `pending` hasta verificar calendario); IRACEXT enteros ≥ 0, vacío = NULL; columnas obligatorias por **nombre**, no posición; repeticiones marcadas, nunca eliminadas ni sumadas.
- IDEAM: nombre `VARIABLE@ESTACION.data` y cabecera `Fecha|Valor`; estación numérica (y existente si hay catálogo); fecha válida y no futura; variable reconocida (`TSSM_MN_D/MX_D/MEDIA_D` = confirmadas, °C; `TSSM_CON`, `PTPM_CON_INTER`, `HR_CAL_MEDIA_D`, `TPR_CAL`, `TV_CAL` = `pending`, D-05); valor numérico, vacío = `missing`; precipitación/humedad no negativas; fechas repetidas = `pending`; cobertura temporal informada sin rellenar huecos. No se aplican rangos de plausibilidad hasta adoptar referencias oficiales.
- DANE: DIVIPOLA de Nariño (`52…`); año 2005–2042; grupo de edad exacto 0–4; población entera ≥ 0, vacía = `missing`. El lector de cada libro DANE (dos diseños distintos) queda pendiente de un mapa de encabezados revisado contra el libro real.

**Transformaciones:** el único procesamiento es normalización de formato (DIVIPOLA a texto de 5 dígitos, recorte de `.0`, fechas a `DATE`) y está versionado en `TRANSFORMATION_VERSION` (se guarda en cada lote). No hay imputación, interpolación, conversión de ausentes a cero ni deduplicación. La bitácora de la auditoría (`reports/`) no se duplica.

**Validar un archivo sin tocar la base de datos** (solo lectura, imprime un resumen JSON):

```powershell
cd backend
python scripts/validate_source.py sivigila RUTA\Datos_2016_995.xlsx --sheet Hoja1
python scripts/validate_source.py ideam RUTA\TSSM_MN_D@52045020.data
```

**Cargar** (aún no autorizado para datos oficiales): `app.importers.loader` expone `get_or_create_source`, `create_batch` y `persist_sivigila|climate|population`. No hacen commit; el llamador abre la transacción y decide `commit`/`rollback`. Ninguna ruta de la API ni el arranque los invocan.

**Pruebas:** `python -m pytest` (SQLite en memoria) cubre validadores, lectores, cargador y las restricciones portables. Las restricciones solo-PostgreSQL (formato por expresión regular de DIVIPOLA y SHA-256), la migración 0001→0003, el downgrade y la ausencia de deriva entre modelos y migraciones se prueban con `tests/test_postgres_schema.py` contra un PostgreSQL **desechable**:

```powershell
$env:RESPIRA_TEST_PG_URL = "postgresql+psycopg://usuario:clave@127.0.0.1:5432/respira_test"   # base vacía; el nombre debe contener test o scratch
python -m pytest tests/test_postgres_schema.py
```

La prueba se omite si la variable no está definida, rechaza hosts de Supabase/pooler y bases no vacías.

**Ubicación de datos:** ver [data/README.md](../../data/README.md). Los originales nunca se versionan.

## Estado actual

El piloto es apto para análisis exploratorio con limitaciones. La integración debe esperar la confirmación de los reportes consecutivos SIVIGILA, la completitud de 2021, los metadatos de calidad y semántica IDEAM y la representatividad territorial de estaciones. El material describe decisiones, no autoriza el paso automático de datos a la app.

## Revisión y versionado

Cambios a este contrato deben incrementar versión, documentar las reglas alteradas y conservar el identificador de lote, el hash de origen cuando exista y la versión de transformación. Una revisión de esquema no cambia el significado retrospectivamente de datos ya importados.
