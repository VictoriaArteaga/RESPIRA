# Limitaciones (qué impide usar registros para entrenamiento)

Estados: **construido** (archivos generados) ≠ **calidad suficiente** ≠ **habilitado para entrenamiento**. Ningún dataset está habilitado para entrenamiento.

1. **Significado del indicador** (INS pendiente): conteo notificado; no es incidencia ni pacientes únicos; el denominador `totcext` no está confirmado.
2. **Reportes repetidos 2012-2018** (INS pendiente): SUMA vs ULTIMO_REPORTE sin interpretación oficial; 17 municipio-semanas con último reporte no determinable.
3. **Calendario**: solo 2016 y 2022 verificados. Las semanas de los otros años no pueden vincularse a fechas ni a IDEAM; las secuencias que cruzan transiciones no validadas quedan sin rezago/objetivo.
4. **2021**: completitud no verificada (conteo oficial INS pendiente). 2020-2021 régimen pandémico.
5. **Ausencias**: 2257 municipio-semanas ausentes y 255 con vacíos; no imputados.
6. **Territorial**: registros con código/departamento incongruente conservados con bandera; registros con departamento NARIÑO y código ajeno o vacío no asignables (ver `v1/registros_territoriales_marcados.csv`).
7. **Población DANE**: salto de serie 2017->2018 sin ajustar; no existe empalme oficial.
8. **Temperatura (V2)**: solo años 2016 y 2022; 1002 municipio-semanas válidas en 10 municipios. Representatividad de la estación para el municipio no validada; ubicación municipal solo por campo del catálogo; Chachagüí sin estación validada; Aldana excluida; series IDEAM sin banderas de calidad.
9. **Precipitación (V3)**: `PTPM_CON_INTER` con significado/unidad pendientes (IDEAM). V3 no contiene precipitación validada.
10. **Tamaño**: muchos municipios tienen medianas semanales bajas (<10), lo que limita la estabilidad de cualquier modelo.

## Qué se necesita para habilitar la versión validada
- INS: interpretación de reportes repetidos, significado de `iracext/totcext`, calendario epidemiológico oficial 2012-2022, conteo oficial 2021.
- IDEAM: significado y unidad de `PTPM_CON_INTER`, banderas de calidad, revisión de la estación 52055230, municipio de ubicación de 52045020.
- DANE: empalme de las series 2005-2017 y 2018-2042.
- Límites municipales (IGAC/DANE) para verificar la ubicación de estaciones.
