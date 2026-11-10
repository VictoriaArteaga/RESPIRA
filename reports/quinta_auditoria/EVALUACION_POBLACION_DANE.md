# Evaluación de la población DANE para RESPIRA

**Fecha:** 5 de noviembre de 2026. Análisis de solo lectura de los libros originales (`..\RESPIRA - copia\data\`). Hashes SHA-256 en el Anexo B de `INFORME_GENERAL.md`.

## 1. Respuesta corta

| Pregunta | Respuesta |
|---|---|
| ¿Qué información poblacional está realmente disponible? | Proyecciones de población por **municipio**, **área** (Cabecera Municipal, Centros Poblados y Rural Disperso, Total), **sexo** y **edad simple**, en dos libros: 2005–2017 y 2018–2042. |
| ¿Hay desagregación por municipio? | **Sí.** 1.122 municipios (2005–2017) y 1.123 (2018–2042); 64 de Nariño en todos los años. |
| ¿Se puede obtener población menor de cinco años? | **Sí**, sumando las edades simples 0, 1, 2, 3 y 4 del área `Total`. |
| ¿Qué años cubre? | 2005–2017 y 2018–2042. Para RESPIRA, 2012–2022 completos: **704/704 municipio-año**. |
| ¿Hay DIVIPOLA? | **Sí**, `MPIO` (5 dígitos) en ambos libros. Coincide con `cod_mun` de SIVIGILA para los 64 municipios. |
| ¿Qué impide calcular tasas epidemiológicas? | Ver sección 5. No es la falta de población; es que el numerador y el denominador miden cosas distintas y que la serie tiene un salto en 2018. |

**El libro nacional `PPED-AreaSexoEdadNac-2018-2070.xlsx` no está disponible** en ninguna de las dos carpetas. La primera auditoría (`data/reports/auditoria_ideam_historico.md`) lo describe como una hoja nacional de 139 × 309 sin departamentos ni municipios. **No se asumió que sus cifras nacionales equivalgan a datos municipales** y no se usó. Tampoco está el libro departamental 2005–2017 que esa auditoría menciona.

## 2. Estructura de los libros

| | Libro 2005–2017 | Libro 2018–2042 |
|---|---|---|
| Archivo | `DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx` (55.969.926 B) | `PPED-AreaSexoEdadMun-2018-2042_VP.xlsx` (131.609.579 B) |
| Hojas | `NuevaMpal` | `Índice`, `PPED`, `PobMunicipalxáreaSexoEdad` |
| Encabezado | Fila 12 (títulos en 6–11) | Filas 8 y 9 (fila 8 con grupos, fila 9 con nombres de campo) |
| Columnas | 267 | 312 |
| Orden de campos territoriales | `DP, DPNOM, DPMP, MPIO, AÑO, ÁREA GEOGRÁFICA` | `DP, DPNOM, MPIO, DPMP, AÑO, ÁREA GEOGRÁFICA` |
| Nombres de edad | `Hombres_0`, `Mujeres_0`, `Total_0` … | `Hombres 0 años`, `Hombres 1 año` … y `Total 0 años` … |
| Registros | 43.758 (1.122 municipios × 13 años × 3 áreas) | 84.225 (1.123 × 25 × 3) según la segunda auditoría; el escaneo de esta auditoría cuenta 4 filas adicionales sin área (notas/pie) |
| Nariño | 2.496 filas (64 × 13 × 3) | 4.800 filas (64 × 25 × 3) |

`DPMP` y `MPIO` **intercambian posición** entre los libros: asignar significado por posición produce errores. Los nombres de columna difieren y deben armonizarse por nombre, no por posición.

## 3. Verificaciones realizadas

- Total 0–4 = suma de hombres 0–4 + mujeres 0–4 en el 100% de las filas de Nariño de ambos libros (0 diferencias).
- Área `Total` = `Cabecera Municipal` + `Centros Poblados y Rural Disperso` en el 100% de las 2.432 filas municipio-año de Nariño (0 diferencias). Por eso **no se pueden sumar las tres áreas**: se duplicaría la población.
- Sin claves `(MPIO, AÑO, ÁREA)` duplicadas, sin nulos en los campos usados.
- 64 municipios en todos los años 2012–2022.
- El piloto: 6/6 valores municipio-año coinciden (Chachagüí 1.023/1.089, Funes 373/389, Samaniego 1.805/1.717 en 2016/2022). Los 33 valores de esos tres municipios entre 2012 y 2022 fueron calculados y son coherentes.
- Códigos de SIVIGILA: 64/64 coinciden con DANE. Excepciones: 1 fila de 2012 con código 52000 y 9 filas con departamento incongruente (ver `INFORME_GENERAL.md`, 3.5).

## 4. Población menor de cinco años de Nariño

| Año | Total Nariño (0–4) | Municipios con <500 | Municipios con <1.000 |
|---:|---:|---:|---:|
| 2012 | 127.179 | 11 | 40 |
| 2013 | 126.593 | 11 | 40 |
| 2014 | 126.309 | 12 | 41 |
| 2015 | 126.297 | 12 | 41 |
| 2016 | 126.502 | 13 | 41 |
| 2017 | 126.835 | 14 | 41 |
| 2018 | 134.253 | 12 | 40 |
| 2019 | 132.765 | 12 | 40 |
| 2020 | 131.685 | 12 | 40 |
| 2021 | 130.720 | 13 | 40 |
| 2022 | 129.879 | 13 | 40 |

Mínimo observado: 283 menores de 5 años (2017). Los 12 municipios con temperatura útil tienen entre 373 (Funes, 2016) y 25.756 (Pasto, 2017); ver Anexo C de `INFORME_GENERAL.md`.

## 5. Qué limita el cálculo de tasas

1. **Salto de serie 2017→2018.** El total de Nariño pasa de 126.835 a 134.253 (+5,85%). Por municipio, la mediana es +8,24%, 53 de 64 municipios suben más de 5% y 3 bajan más de 5%. Dentro de cada libro las variaciones anuales son pequeñas (mediana −0,19% entre 2016 y 2017; −1,66% entre 2018 y 2019). Es un cambio de libro y de base de proyección (2018–2042 está actualizado a julio de 2025), no una evolución demográfica. Ejemplos: Tumaco 25.092 → 28.366; Chachagüí 1.042 → 1.122; Pasto 25.756 → 25.104 (sentido contrario). Una tasa o una variable demográfica sin marcar esta ruptura la presenta al modelo como señal.
2. **Municipios muy pequeños.** 13 municipios tienen menos de 500 menores de 5 años en 2022 y 40 tienen menos de 1.000. Con la mediana semanal de IRA de 1–10 en esos municipios, una tasa semanal es casi puro ruido de conteos pequeños.
3. **Numerador y denominador no son comparables.** El numerador es lo notificado por las UPGD que reportan (consulta externa/urgencias, por municipio *notificador*); el denominador es población proyectada del municipio. Los niños atendidos en otro municipio, la cobertura de reporte y el aseguramiento no están en el denominador. La tasa cruda del piloto (454/1.023 en Chachagüí 2016, 0,44 por niño-año) es demasiado baja para ser incidencia de IRA.
4. **Granularidad anual.** La población es una proyección anual; asignarla a las semanas del año supone constancia dentro del año, y el año epidemiológico no coincide con el calendario en los bordes (SE1 de 2018 empieza el 31/12/2017).
5. **Revisiones de la proyección.** Los libros llevan marca de versión (`_VP`; hoja `PPED` con actualización de julio de 2025). Una descarga futura puede cambiar las cifras: hay que guardar versión y hash junto con la población.
6. **No hay estimación de población en riesgo** (afiliados, con acceso a UPGD) ni por edad en semanas.

## 6. Reglas de uso propuestas (a aprobar)

1. Usar siempre `Área = Total` y la suma de `Total_0..Total_4` (alternativamente hombres + mujeres de cada edad, nunca ambos).
2. Conservar `MPIO` como texto de 5 caracteres y guardar libro de origen, versión y hash.
3. Armonizar los dos libros **por nombre de columna**, no por posición.
4. Agregar un indicador de libro (`dane_libro`: 2005–2017 / 2018–2042) para que el salto sea visible.
5. No calcular tasas semanales en municipios con <500 menores de 5 años; si se calculan, hacerlo con intervalos o agregando municipios.
6. Denominador solo después de aprobar la decisión 1 de `INFORME_GENERAL.md` (indicador).

## 7. Qué quedaría sin resolver

- El libro nacional y el departamental (no disponibles): no son necesarios para un dataset municipal.
- Si DANE publica un empalme oficial de la serie 2005–2017 con la base 2018, resolvería el salto. No se encontró localmente.
- La proyección municipal no distingue cabecera de rural en el modelo actual; el área `Total` es suficiente para el primer dataset.
