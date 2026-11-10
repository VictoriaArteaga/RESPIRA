# Auditoría de integridad SIVIGILA 995, 2021

## Inventario disponible

En la carpeta local autorizada `data/SIVIGILA` se encontró una versión: `Datos_2021_995.xlsx`, 77,043,344 bytes, hoja `ACUMULADO`, dimensiones 1,048,576 filas × 85 columnas. La fila de encabezado es la 2 y la primera fila contiene rótulos parciales. El archivo alcanza exactamente el límite Excel de 1,048,576 filas. La lista completa de versiones/localización está registrada por el script y la salida de integridad de fuentes.

No se encontró en la carpeta SIVIGILA local otra versión 2021 en CSV, XLS, XLSX separado/fragmentado, Parquet o base de datos. No hay registro de exportación que informe cantidad previa de filas, número de páginas/particiones, conteo de origen, fecha de descarga verificable ni checksum oficial. Los metadatos internos del libro, aun si existen, no son prueba suficiente de integridad.

## Resultado

**Integridad no demostrada; año 2021 no validado.** El límite de filas genera sospecha real de truncamiento, pero no prueba por sí mismo que haya truncamiento: podría haber exactamente ese número de filas incluyendo título y encabezado, o el libro pudo recortarse. Abrir el XLSX, observar que tiene datos, o tomar el máximo de fila como conteo no resuelve esa incertidumbre.

No se reconstruyó ni consolidó el año porque falta otra versión independiente y no existe una clave que demuestre que archivos hipotéticos fragmentados serían particiones sin traslape. 2021 debe excluirse de cualquier integración que requiera completitud demostrada, hasta obtener del INS/entidad que entregó el archivo un export alterno, conteo de origen o checksum y aclaración de la fila final. Se conserva sin modificación el XLSX original.
