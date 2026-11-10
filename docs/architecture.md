# Arquitectura y siguientes integraciones

## Operación actual

La API FastAPI organiza rutas, servicios de dominio, repositorios SQLAlchemy y modelos. El frontend consume la API a través de `src/services/api.ts`; Electron limita el acceso del renderer a solicitudes GET autorizadas mediante IPC. La persistencia es PostgreSQL (Supabase, Session Pooler) configurado con variables `DB_*`.

El conjunto cargado desde `backend/data/simulated/ira_cases.csv` se valida para exigir la etiqueta `DATOS SINTÉTICOS DE PRUEBA`. No se debe mezclar con información oficial sin identificar y validar su origen.

## PostgreSQL

La conexión usa el controlador `postgresql+psycopg` y se configura en `backend/.env`. Los modelos y repositorios SQLAlchemy son la capa de persistencia. El esquema se gestiona solo con Alembic (nunca `create_all` en producción). La carga oficial de datos no está habilitada: requiere autorización explícita y una ejecución manual del cargador.

## Capa de integración de datos (Fase 2.2)

`ira_cases` es el **modelo inicial de la aplicación**: la app y sus pruebas dependen de él (clima obligatorio por municipio, sin procedencia ni estado de calidad) y por eso no se modifica (`municipalities` solo gana `divipola_code` opcional y coordenadas opcionales). Los datos reales entran por un modelo separado en el esquema `public`, migración `0003`:

```
FUENTE ORIGINAL (data/, solo lectura, fuera de Git)
  -> LECTURA por fuente (app/importers/{sivigila,ideam,dane}.py)
  -> VALIDACIÓN por fila (estado valid | pending | rejected | missing | derived + hallazgos)
  -> CARGA con trazabilidad (data_source -> import_batch -> filas con hoja/fila de origen -> data_quality_issue)
  -> [futuro] dataset analítico derivado, con versión de reglas
```

Tablas: `data_source`, `import_batch`, `weather_station`, `sivigila_report`, `climate_observation`, `annual_population`, `data_quality_issue`. Detalle, reglas y ejecución en [data-integration/README.md](data-integration/README.md). Los agregados (`weekly_ira_indicator`, resúmenes por estación) y cualquier tasa quedan fuera hasta cerrar D-01, D-02 y D-15; mientras tanto, la API y el dashboard siguen leyendo solo `ira_cases`.

## SIVIGILA

La incorporación futura debe implementarse como un proceso de ingestión separado: recepción autorizada, validación del esquema, normalización territorial y temporal, trazabilidad de fuente, controles de calidad y revisión antes de insertar. No existe una conexión ni se incluyen datos oficiales en este repositorio.

## Inteligencia artificial

La IA permanece desactivada. Alertas y niveles actuales son cálculos deterministas del servicio de riesgo, con umbrales documentados y sin inferencia. Una futura capacidad analítica debe integrarse detrás de un servicio independiente, con entradas/salidas tipadas, configuración explícita y controles de evaluación; no debe reemplazar estas reglas ni presentarse como activa hasta que exista implementación y validación.
