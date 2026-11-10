# Resultado automático de la cuarta auditoría

- Validaciones PASS: 47
- Validaciones FAIL: 0
- Advertencias/pendientes: 6

## Fallos

Ninguno.

## Advertencias y confirmaciones pendientes

- `SIV_WEEKS_2016` (SIVIGILA): 152 de 156 municipio-semanas con filas; 4 sin filas. {"Chachagüí": [44, 52], "Funes": [11, 21], "Samaniego": []}
- `SIV_SCHEMA_DIFF` (SIVIGILA): columnas 2016=84; 2022=83; solo2016=1; solo2022=0. 2016-only=['version']; 2022-only=[]
- `SIV_REPEATED_PROVIDER_WEEK` (SIVIGILA): 1 grupos con varias filas por municipio-año-semana-UPGD-sede; se conservan. La clave completa incluye NUM_CON; consulte filas_repeticion_sivigila.csv; no llamar duplicado solo por proveedor-semana
- `SIV_2021_INTEGRITY` (SIVIGILA 2021): 1 versión(es) local(es); workbook metadata={"sheets": [{"name": "ACUMULADO", "rows": 1048576, "cols": 85, "header_row": 2, "header_fields_n": 85, "has_event_week_fields": true}], "created": "2022-04-27 22:12:33", "modified": "2022-05-02 21:00:02", "creator_metadata_present": true}. Una hoja alcanza límite XLSX; no se encontró prueba independiente de integridad ni archivo alternativo
- `IDEAM_PLAUSIBILITY_RANGES` (IDEAM): No se aplicó un rango duro de plausibilidad. La documentación consultada no define umbral de plausibilidad por estación aplicable a estas extracciones; los extremos se conservan para revisión y no se eliminan automáticamente
- `FUNES_2022_LOW_COVERAGE` (IDEAM): Semanas de Funes 2022 debajo de 6/7 días identificadas. TSSM_MN_D: 5;52; TSSM_MX_D: 5;52; TSSM_MEDIA_D: 5;52

## Interpretación

PASS indica una comprobación reproducible de estructura/consistencia local; no certifica validez epidemiológica, climatológica o científica. WARNING/PENDING requiere revisión documental o confirmación de fuente. Los datos fuente se abren en modo lectura y las salidas se escriben solo en esta carpeta.
