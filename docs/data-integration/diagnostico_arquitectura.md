# Diagnóstico de arquitectura para la integración RESPIRA

**Inspección:** 2026-10-26 · **Rama observada:** `master` (no `main`/`develop`). La inspección de Git encontró `data/`, `docs/data-audit/`, `reports/` y `pytest.ini` sin seguimiento. Se conservaron; no se limpió ni se descartó ese estado.

## Arquitectura vigente

- **Escritorio:** Electron + React/TypeScript + Vite. El renderer consume endpoints GET a través de `frontend/src/services/api.ts`; Electron usa un puente IPC de lectura.
- **API:** FastAPI. Rutas, schemas Pydantic, servicios y repositorios SQLAlchemy están separados en `backend/app/api/`, `schemas/`, `services/`, `repositories/` y `models/`.
- **Persistencia actual:** `backend/app/core/database.py` crea un engine desde `DATABASE_URL`, con SQLite local por defecto. `backend/app/core/seed.py` carga `backend/data/simulated/ira_cases.csv` solo si la tabla `ira_cases` está vacía y exige la etiqueta `DATOS SINTÉTICOS DE PRUEBA`.
- **Modelo actual:** `IraCase` tiene `cases`, `temperature`, `precipitation` y `humidity` como valores obligatorios en el ORM y schemas. `Municipality` usa un id interno y nombre como clave única; no está modelado DIVIPOLA como clave canónica ni existe calendario de fechas.
- **Presentación:** los tipos del frontend (`frontend/src/types/case.ts`) también esperan casos y las tres variables climáticas como números no nulos. Las alertas y el canal endémico son reglas estadísticas deterministas sobre los datos cargados; no son un servicio de IA.
- **Fuentes auditadas:** los libros originales están bajo `data/SIVIGILA/`, los extractos IDEAM bajo carpetas `.data`, y DANE/catálogos dentro de `data/`. Los informes y el piloto están en `reports/` y `data/processed/pilot/`. Los scripts de auditoría están bajo `data/scripts/`.

## Puntos futuros de integración

1. Un proceso de ingestión separado de `seed_simulated_data`, que solo reciba lotes autorizados, preserve los originales fuera de la base operativa y valide esquema/huellas.
2. Un staging normalizado y restringido para filas colectivas SIVIGILA, con identificador de fila fuente, código municipal, período epidemiológico, campos permitidos y referencia al lote.
3. Entidades separadas para observaciones IDEAM, resúmenes meteorológicos derivados, población anual DANE y calendario epidemiológico.
4. Una capa de servicio/repositorio futura que lea agregados aceptados y exponga esquemas API capaces de expresar `NULL`, estado de cobertura y procedencia. La interfaz no se rediseña en esta fase.
5. Una futura migración PostgreSQL versionada y revisada, solo después de cerrar los criterios de aceptación. El SQL entregado ahora es un diseño; no existe migración activa.

## Inconsistencias a resolver antes de mapear el piloto a la app

- La tabla actual mezcla observación epidemiológica y clima en una fila y exige precipitación/humedad aun cuando esas variables están excluidas o no confirmadas.
- `cases` no conserva que el dato SIVIGILA es conteo colectivo de pacientes reportados en consulta externa por grupo etario; tampoco distingue reportado cero de semana sin filas.
- El modelo actual no conserva código DIVIPOLA, libro/hoja/fila fuente, versión de esquema, lote/hash, estación fuente ni calidad desconocida.
- No hay calendario con fechas de inicio/fin por año y semana. El piloto validó semanas 1–52 de 2016 y 2022; otros años pueden tener SE 53.
- La granularidad de `NUM_CON` permite reportes sucesivos de una UPGD en una misma semana. No se ha confirmado si son aditivos o correcciones; por ello no se propone unicidad por proveedor-semana.
- El dataset actual cargado por seed es sintético. No debe mezclarse ni presentarse como importación oficial.

## Archivos de especificación

Se crean siete artefactos nuevos en `docs/data-integration/`: este diagnóstico, README, diccionario, modelo, contrato, plan, criterios y SQL de referencia (ocho documentos incluyendo README). Se complementa `reports/decisiones_pendientes_datos.md` con prioridad y criterios de cierre sin eliminar las filas previas. No se modifica código de aplicación, dependencias, configuración, datos fuente ni informes de auditorías anteriores.

## Límites

La inspección cubre arquitectura y contratos locales pertinentes, no una revisión funcional completa de todos los componentes ni un ensayo de despliegue. No se ejecutó importación ni SQL; no se abrió una conexión de base de datos.
