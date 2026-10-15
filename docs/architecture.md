# Arquitectura y siguientes integraciones

## Operación actual

La API FastAPI organiza rutas, servicios de dominio, repositorios SQLAlchemy y modelos. El frontend consume la API a través de `src/services/api.ts`; Electron limita el acceso del renderer a solicitudes GET autorizadas mediante IPC. SQLite es el modo local predeterminado y las variables `DATABASE_URL` permiten configurar PostgreSQL sin cambiar los servicios.

El conjunto cargado desde `backend/data/simulated/ira_cases.csv` se valida para exigir la etiqueta `DATOS SINTÉTICOS DE PRUEBA`. No se debe mezclar con información oficial sin identificar y validar su origen.

## PostgreSQL

Para usar PostgreSQL, configurar `DATABASE_URL` en un `.env` local con el controlador `postgresql+psycopg`. Los modelos y repositorios SQLAlchemy son la capa de persistencia. La conexión productiva, migraciones, credenciales gestionadas y carga oficial de datos no están habilitadas en esta versión académica.

## SIVIGILA

La incorporación futura debe implementarse como un proceso de ingestión separado: recepción autorizada, validación del esquema, normalización territorial y temporal, trazabilidad de fuente, controles de calidad y revisión antes de insertar. No existe una conexión ni se incluyen datos oficiales en este repositorio.

## Inteligencia artificial

La IA permanece desactivada. Alertas y niveles actuales son cálculos deterministas del servicio de riesgo, con umbrales documentados y sin inferencia. Una futura capacidad analítica debe integrarse detrás de un servicio independiente, con entradas/salidas tipadas, configuración explícita y controles de evaluación; no debe reemplazar estas reglas ni presentarse como activa hasta que exista implementación y validación.
