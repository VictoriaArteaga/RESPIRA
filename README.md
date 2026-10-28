# RESPIRA

Aplicación de escritorio académica para apoyar el monitoreo de infecciones respiratorias agudas en menores de cinco años en Nariño.

## Semanas 3 y 4

- Mapa Leaflet con marcadores de los municipios incluidos en el conjunto de datos y filtros por año y semana. El color muestra una comparación estadística del valor observado frente a la media de la misma semana en años previos: bajo (<20% por encima), moderado (20% a <50%) y alto (≥50%).
- Canal endémico con casos observados, mediana, percentiles 25, 75 y 90, y estadísticas descriptivas para municipio y año seleccionados.
- Ambas vistas consumen la API FastAPI y muestran estados de carga, error y ausencia de datos.

El mapa presenta ubicaciones municipales; el dataset no contiene polígonos de límites municipales. Los registros son **sintéticos de desarrollo**, no son datos oficiales de SIVIGILA. El proyecto no implementa IA, aprendizaje automático ni predicciones futuras. Los niveles son referencias estadísticas para apoyo al monitoreo y no constituyen diagnóstico médico.

Consulta [backend/README.md](backend/README.md) y [frontend/README.md](frontend/README.md) para instalación y ejecución.

El backend usa PostgreSQL (Supabase) configurado mediante variables `DB_*` en `backend/.env`. Las alertas actuales usan reglas deterministas. La integración oficial SIVIGILA y cualquier IA están pendientes y no se simulan. Consulta [docs/architecture.md](docs/architecture.md) para los límites de arquitectura y fases futuras.
