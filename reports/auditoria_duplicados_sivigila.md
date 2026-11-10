# Auditoría del registro repetido por proveedor-semana

## Hallazgo

En Chachagüí (DIVIPOLA 52240), año epidemiológico 2016, semana 43, el libro fuente tiene dos filas con la misma combinación municipio-año-semana-UPGD-sede: `COD_PRE=5224001399`, `COD_SUB=01`. Las filas están en `Datos_2016_995.xlsx`, hoja `Hoja1`, filas Excel 204616 y 207474. Los valores analíticos relevantes son:

| Fila | `NUM_CON` | `IRACEXT_1` | `IRACEXT_2` | `IRACEXT_3` | Suma 0–4 |
|---:|---:|---:|---:|---:|---:|
| 204616 | 263 | 4 | 0 | 4 | 8 |
| 207474 | 264 | 0 | 0 | 1 | 1 |

No son filas idénticas: tienen consecutivos distintos y vectores de conteos distintos. La suma semanal piloto es 9 y conserva ambas. La evidencia reproducible, sin campos de contacto ni otros atributos identificables, está en [`reports/cuarta_auditoria/filas_repeticion_sivigila.csv`](cuarta_auditoria/filas_repeticion_sivigila.csv).

## Regla y granularidad

El detector agrupa por `(COD_MUN, AÑO, SEMANA, COD_PRE, COD_SUB)` para localizar varias filas de un mismo proveedor y sede en la misma semana. **Ese grupo no es clave única de registro.** La estructura de registros colectivos INS especifica que `NUM_CON` es un consecutivo asignado para cada reporte generado por la misma UPGD en la misma semana y evento; `COD_PRE` identifica prestador y `COD_SUB` sede/territorio. En este caso `NUM_CON` es 263 frente a 264, por lo que existen dos reportes numerados separadamente conforme a la definición documentada. Fuente: [INS, estructura de registros SIVIGILA 2016, datos colectivos](https://www.ins.gov.co/Direcciones/Vigilancia/sivigila/Documents/Anexo%202%20Estructura%20de%20los%20registros%20de%20notificaci%C3%B3n.pdf), que también publica la versión 2018–2020 del diccionario con la misma regla para `NUM_CON`: [INS, diccionario 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf).

## Conclusión y decisión

- **Duplicado exacto de fila:** no; campos analíticos diferentes y consecutivos distintos.
- **Clave completa repetida al incluir `NUM_CON`:** no se detectó en los grupos observados de 2016 y 2022.
- **Dos reportes del mismo proveedor en la misma semana:** sí; está permitido por la definición de consecutivo por reporte.
- **¿Prueba esto doble conteo?** No. La documentación disponible no explica si uno de los reportes puede ser una corrección que reemplaza al anterior, ni establece cómo consolidar sucesivos reportes en la extracción local. Tampoco demuestra que sean dos cargas acumulables.
- **Acción:** conservar ambas filas en el insumo observado, mantener suma 9 solo como agregación exploratoria y marcar el grupo como `REPETICION_PROVEEDOR_SEMANA_REVISAR_CONSOLIDACION`; no deduplicar ni interpretar el 9 como definitivo hasta aclaración del INS/ET.

En 2022 no se detectaron grupos múltiples por esa misma combinación en los tres municipios del piloto. La auditoría solo cubre esos municipios y años, no todos los renglones históricos de los 11 libros.
