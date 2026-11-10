# Auditoría IDEAM histórica y evaluación DANE para RESPIRA

Fecha de auditoría: 2026-10-25. Fuentes originales inspeccionadas en modo de solo lectura.

## Resumen ejecutivo

Los dos archivos `descargaDhime*.csv` son idénticos byte por byte (SHA-256 igual) y contienen 58 filas sobre una sola estación-variable-parámetro por registro: `TEMPERATURA` / `Temperatura máxima absoluta anual`, unidad `degC`. Cubren cinco estaciones de Nariño entre 2013 y 2026, con disponibilidad irregular en una de ellas. La fecha se repite el 1 de enero de cada año y la cadencia observada es anual; por tanto estos archivos **no permiten construir variables climáticas semanales**, aunque el parámetro sea meteorológico y varias estaciones tengan registros en 2012–2022. No incluyen temperatura mínima/media, precipitación ni humedad.

El CNE IDEAM confirma por código que las cinco estaciones pertenecen a Nariño. Los dos libros DANE disponibles son de niveles distintos: una serie **departamental** para 2005–2017 y una serie **nacional** para 2018–2070. Ninguno contiene municipios ni DIVIPOLA; no se puede construir `poblacion_menor_5` municipal. No se generó un CSV piloto municipal porque los datos necesarios no existen en los archivos revisados.

Conclusión para RESPIRA: hay insumos estructurales de SIVIGILA 995 para 2012–2022, pero IDEAM histórico y DANE municipal siguen siendo insuficientes. No comenzar todavía la integración a nivel municipio-semana.

## 1. Archivos y entorno inspeccionados

| Archivo | Tamaño | Dimensión/hojas | Contenido o periodo | Observación|
|---|---|---|---|---|
| descargaDhime 2.csv | 7,307 bytes | 58 × 8 | 2013-01-01 a 2026-01-01 | DHIME, registros anuales |
| descargaDhime.csv | 7,307 bytes | 58 × 8 | 2013-01-01 a 2026-01-01 | Copia idéntica del anterior |
| CNE_IDEAM.xls | 2,090,496 bytes | 1 hoja; 4,523 × 20 incl. encabezado | Catálogo nacional de estaciones | Lectura Excel solo lectura; hoja CNE |
| NARI_O.csv | 44,574 bytes | 336 × 11 | Catálogo subset Nariño | Códigos repetidos/padding; usar CNE validado |
| DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx | 2,414,196 bytes | 1 hoja; 1,299 × 310 | 2005–2017 | Proyección a nivel departamental |
| PPED-AreaSexoEdadNac-2018-2070.xlsx | 341,148 bytes | 3 hojas; hoja de datos 139 × 309 | 2018–2070 | Proyección a nivel nacional |

Los CSV meteorológicos se analizaron por separado de `Datos_de_Estaciones_de_IDEAM_y_de_Terceros.csv`; ese otro archivo es una extracción nacional de observaciones del 25-10-2026 y no se mezcló con los dos históricos DHIME. El catálogo CNE se usó únicamente para resolver estación→municipio por código. No se alteró, renombró, movió ni combinó físicamente ningún original.

### Catálogo CNE usado para el cruce

El `.xls` tiene hoja `CNE` y encabezados en la fila 1: `CODIGO`, `NOMBRE`, `CATEGORIA`, `TECNOLOGIA`, `ESTADO`, `FECHA_INSTALACION`, `FECHA_SUSPENSION`, `ALTITUD`, `LATITUD`, `LONGITUD`, `DEPARTAMENTO`, `MUNICIPIO`, `AREA_OPERATIVA`, `ENTIDAD`, `AREA_HIDROGRAFICA`, `ZONA_HIDROGRAFICA`, `SUBZONA_HIDROGRAFICA`, `CORRIENTE`, `OBSERVACION`, `SUBRED`. La hoja contiene 4,522 estaciones (códigos únicos; no se encontraron duplicados de código en esta hoja). Nariño: 126 estaciones en 47 etiquetas municipales; estados: 87 activas, 32 suspendidas, 7 en mantenimiento. Coordenadas presentes en las 126 filas de Nariño. Esas 47 etiquetas no equivalen necesariamente al total de municipios del departamento; no se comparó contra un catálogo DIVIPOLA local.

`NARI_O.csv` contiene 336 filas y 168 códigos distintos y no coincide en conteos con el CNE. En varios casos sus códigos de ocho dígitos aparecen rellenados a diez posiciones con ceros iniciales. Los cinco cruces de esta auditoría se resolvieron con el código de estación del CNE; no se unieron por aproximación de nombres. El CNE y `NARI_O.csv` son productos/listados de distinto alcance o versión, por lo que sus conteos no deben mezclarse.

## 2. Inspección de los dos CSV históricos IDEAM

### Estructura

Los dos archivos tienen los ocho encabezados `CodigoEstacion`, `NombreEstacion`, `Variable`, `Parametro`, `Fecha`, `Unidad`, `Valor`, `NivelAprobacion`. Tipos para análisis: código como texto; nombres/etiquetas/unidad/nivel como texto; fecha interpretada desde `dd/mm/YYYY HH:MM`; valor numérico decimal. 58 registros por archivo, 5 códigos y nombres, 1 variable, 1 parámetro, 14 fechas/años, 1 unidad y 2 niveles de aprobación. Cero nulos en cualquiera de las ocho columnas, cero filas duplicadas dentro de cada archivo y cero duplicados por `CodigoEstacion+Variable+Parametro+Fecha`.

Los códigos históricos contienen 8 dígitos en los cinco casos; no hay nulos ni códigos inválidos. Se conservaron como texto. Las 58 fechas se interpretaron correctamente, todas a las 00:00 del 1 de enero; no hay fechas futuras a la fecha de auditoría. El año 2026, sin embargo, está incompleto al 25 de octubre: la etiqueta “anual” y el nivel de aprobación no prueban que ya incluya el cierre de todo el año. Debe validarse antes de usar esa observación como máximo anual final.

### Primeras 10 filas del archivo (campos clave)

| Código estación | Variable | Parámetro | Fecha | Valor | Nivel|
|---|---|---|---|---|---|
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2013 00:00 | 31.2 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2014 00:00 | 30.3 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2015 00:00 | 31.2 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2016 00:00 | 31.3 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2017 00:00 | 29.2 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2018 00:00 | 29.8 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2019 00:00 | 29.9 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2020 00:00 | 29.4 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2021 00:00 | 28.8 | Definitivo |
| 52045020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2022 00:00 | 29.6 | Definitivo |

### Últimas 10 filas del archivo (campos clave)

| Código estación | Variable | Parámetro | Fecha | Valor | Nivel|
|---|---|---|---|---|---|
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2020 00:00 | 22.8 | Preliminar |
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2021 00:00 | 22.4 | Preliminar |
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2022 00:00 | 22.4 | Preliminar |
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2023 00:00 | 23.8 | Preliminar |
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2024 00:00 | 24.0 | Preliminar |
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2025 00:00 | 23.8 | Preliminar |
| 52055210 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2026 00:00 | 24.0 | Preliminar |
| 51035020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2013 00:00 | 32.4 | Preliminar |
| 51035020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2016 00:00 | 32.6 | Preliminar |
| 51035020 | TEMPERATURA | Temperatura máxima absoluta anual | 01/01/2017 00:00 | 32.0 | Preliminar |

### Variable y parámetro encontrados

| Variable | Parámetro | Registros | Estaciones | Fecha inicial | Fecha final | Unidades | Frecuencia observada|
|---|---|---|---|---|---|---|---|
| TEMPERATURA | Temperatura máxima absoluta anual | 58 | 5 | 2013-01-01 | 2026-01-01 | degC | ANUAL; una marca por estación-año disponible |

No se encontró ninguna categoría `PRECIPITACION`, `HUMEDAD` ni otro parámetro de temperatura. “Temperatura máxima absoluta anual” representa un extremo anual según la etiqueta del parámetro; no debe tratarse como temperatura máxima semanal ni como media anual. Esta lectura se apoya en el valor de `Parametro` y en las fechas observadas, todas el 1 de enero con intervalos interanuales.

### Distribución anual de registros

| Año | Registros|
|---|---|
| 2013 | 5 |
| 2014 | 4 |
| 2015 | 4 |
| 2016 | 5 |
| 2017 | 5 |
| 2018 | 4 |
| 2019 | 4 |
| 2020 | 4 |
| 2021 | 4 |
| 2022 | 4 |
| 2023 | 4 |
| 2024 | 4 |
| 2025 | 4 |
| 2026 | 3 |

Cobertura para la ventana SIVIGILA 2012–2022 (SI = existe al menos un registro en ese año):

| Variable / parámetro | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022|
|---|---|---|---|---|---|---|---|---|---|---|---|
| TEMPERATURA / Temperatura máxima absoluta anual | NO | SI | SI | SI | SI | SI | SI | SI | SI | SI | SI |

Por estación, la cobertura del periodo 2012–2022 es:

| Código | Municipio | N.º registros 2012–22 | Años disponibles 2012–22|
|---|---|---|---|
| 51035020 | Tumaco | 3 | 2013, 2016, 2017 |
| 52045020 | Chachagüí | 10 | 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 |
| 52055030 | Consacá | 10 | 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 |
| 52055210 | Pasto | 10 | 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 |
| 52055230 | Aldana | 10 | 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 |

2012 no aparece en los dos CSV. Entre 2013 y 2022 hay 43 registros: cuatro estaciones tienen un dato en cada uno de esos diez años y `51035020` solo en 2013, 2016 y 2017. Hay 15 registros posteriores a 2022 (2023–2026), fuera de la ventana inicial.

### Estaciones de Nariño relacionadas por código

| Código CNE | Nombre de estación | Municipio | Departamento | Latitud | Longitud | Altitud m | Categoría CNE | Estado CNE | Registros | Periodo total|
|---|---|---|---|---|---|---|---|---|---|---|
| 51035020 | CCCP DL PACIFICO | Tumaco | Nariño | 1.8191666670 | -78.7300000000 | 1 | Climatológica Principal | Activa | 3 | 2013–2017 (3 años) |
| 52045020 | AEROPUERTO ANTONIO NARIÑO | Chachagüí | Nariño | 1.3940833330 | -77.2908611100 | 1796 | Sinóptica Principal | Activa | 14 | 2013–2026 (14 años) |
| 52055030 | BOMBONÁ | Consacá | Nariño | 1.1843611110 | -77.4651111100 | 1493 | Climatológica Ordinaria | En Mantenimiento | 13 | 2013–2025 (13 años) |
| 52055210 | BOTANA - AUT | Pasto | Nariño | 1.1600000000 | -77.2788055600 | 2820 | Climatológica Principal | Activa | 14 | 2013–2026 (14 años) |
| 52055230 | AEROPUERTO SAN LUIS - AUT | Aldana | Nariño | 0.8570833330 | -77.6777500000 | 2961 | Sinóptica Principal | Activa | 14 | 2013–2026 (14 años) |

Las 5 estaciones históricas pertenecen a Nariño: 51035020 (Tumaco), 52045020 (Chachagüí), 52055030 (Consacá), 52055210 (Pasto), 52055230 (Aldana). En 2012–2022 solo la estación de Consacá aparece en mantenimiento en el estado actual del CNE; ese estado actual no describe automáticamente su estado histórico. Categoría y estado tampoco prueban qué sensor produjo cada observación ni la continuidad del parámetro.

### Nivel de aprobación y calidad

| NivelAprobacion | Registros | Porcentaje|
|---|---|---|
| Preliminar | 44 | 75.9% |
| Definitivo | 14 | 24.1% |

14/58 (24.1%) aparecen como `Definitivo`; 44/58 (75.9%) como `Preliminar`. Los 14 definitivos corresponden a la estación 52045020; las otras cuatro tienen registros preliminares. No se excluyó ningún nivel.

| Estadístico de Valor (degC) | Resultado|
|---|---|
| min | 19.8 |
| max | 32.7 |
| mean | 26.591 |
| median | 29.0 |
| std | 4.623 |
| p1 | 20.028 |
| p99 | 32.643 |

Valores observados: mínimo 19.8 °C, máximo 32.7 °C, media 26.591 °C, mediana 29.0 °C, desviación estándar 4.623 °C, percentiles 1 y 99 de 20.028 °C y 32.643 °C. No hay ceros, valores negativos, faltantes ni valores extremos obvios con esta revisión global; esos rangos no son por sí solos criterio de validez porque las estaciones tienen altitudes de 1 a 2,961 m. No se eliminaron ni filtraron valores.

Tipos de posible anomalía temporal: 51035020 tiene huecos de varios años; 2026 es un año aún no terminado; todos los datos aparecen en fecha nominal 1 de enero con parámetro anual. Hace falta confirmar en DHIME cómo interpreta `Fecha` en agregados anuales y el criterio de `NivelAprobacion`.

### Comparación entre los dos archivos

Los archivos tienen igual tamaño (7,307 bytes), igual hash SHA-256 (`71a7357f0d4d594979b29676548e98a509310d66d2b326d269fba92959d32bce`) y bytes idénticos. Cada archivo contiene 58 filas. Unirlos duplicaría todos los 58 registros; no son fuentes complementarias ni una ampliación temporal/geográfica. Mantener ambos originales sin cambios y, para análisis, usar solo una copia lógica con trazabilidad al nombre de origen. No borrar la copia.

## 3. Evaluación de utilidad climática semanal

| Variable candidata | Existe en CSV DHIME | Estaciones Nariño | Cobertura 2012–22 | Resolución observada | ¿Sirve para semana RESPIRA?|
|---|---|---|---|---|---|
| Temperatura máxima absoluta anual | Sí; 1 parámetro | 5; solo 4 con cobertura anual completa 2013–22 | 2013–2022 parcial; no 2012 | Anual | No; un extremo anual no se desagrega correctamente a semanas. |
| Temperatura mínima | No | 0 | No | Ausente | No; obtener parámetro de mínima diaria/hora. |
| Temperatura media | No | 0 | No | Ausente | No; obtener medias diarias o subdiarias. |
| Precipitación | No | 0 | No | Ausente | No; falta precipitación diaria/subdiaria para acumulado semanal. |
| Humedad relativa | No | 0 | No | Ausente | No; falta humedad diaria/subdiaria. |

Para una futura agregación semanal serían necesarios datos originales diarios u horarios con estación, fecha real de observación, unidad, banderas de calidad y continuidad suficiente. Con datos diarios validados podrían calcularse, por estación y semana epidemiológica, máximas/mínimas/medias y acumulados según la definición de cada variable; con registros anuales de extremos no se puede reconstruir una secuencia semanal. Interpolar o repartir los máximos anuales entre semanas fabricaría precisión que los archivos no contienen y no se recomienda.

## 4. Auditoría de los dos archivos DANE

### Archivo departamental DANE 2005–2017

`DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx` tiene una hoja `Departamental_2005-2017` con rango A7:KX1299 (1,299 filas × 310 columnas). Hay títulos en filas 7–9, encabezado real en fila 12 y datos desde fila 13. Presenta dos celdas combinadas (`A7:L8`, `A9:L9`). Columnas: `DP`, `DPNOM`, `AÑO`, `ÁREA GEOGRÁFICA`; bloques `Hombres_0…Hombres_100`, `Mujeres_0…Mujeres_100`, `Total_0…Total_100`; y totales de hombres, mujeres y general. La estructura de edad es edad simple por sexo y total. `DP` es código departamental de dos caracteres (se conserva como texto); no hay `COD_MPIO`, municipio ni DIVIPOLA municipal.

Contiene 1,287 filas de datos (33 entidades territoriales × 13 años × 3 áreas: `Cabecera`, `Centros Poblados y Rural Disperso`, `Total`), años 2005–2017. `DP`/`DPNOM` son departamento/distrito, no municipio. Para población 0–4 por departamento se puede sumar `Total_0`…`Total_4` usando solo `ÁREA GEOGRÁFICA=Total`, o sumar Hombres y Mujeres en esas edades, pero nunca ambas representaciones ni las tres áreas juntas. Es proyección departamental, no una observación municipal.

Como ejemplo departamental (no municipal), Nariño, `DP=52`, `ÁREA GEOGRÁFICA=Total`, suma de `Total_0` a `Total_4`:

| Año | Nariño departamento, población proyectada 0–4|
|---|---|
| 2005 | 139,360 |
| 2006 | 136,957 |
| 2007 | 134,723 |
| 2008 | 132,689 |
| 2009 | 130,907 |
| 2010 | 129,395 |
| 2011 | 128,105 |
| 2012 | 127,179 |
| 2013 | 126,593 |
| 2014 | 126,309 |
| 2015 | 126,297 |
| 2016 | 126,502 |
| 2017 | 126,835 |

Estos valores no sustituyen población por municipio: no pueden distribuirse entre municipios sin datos de detalle. El libro cubre Nariño solo hasta 2017.

Filas de datos iniciales y finales inspeccionadas —se muestran claves y suma 0–4, no los 310 valores de edad por fila—:

| DP | Departamento | Año | Área | Población 0–4 del área|
|---|---|---|---|---|
| 05 | Antioquia | 2005 | Cabecera | 323731 |
| 05 | Antioquia | 2005 | Centros Poblados y Rural Disperso | 169763 |
| 05 | Antioquia | 2005 | Total | 493494 |
| 05 | Antioquia | 2006 | Cabecera | 319618 |
| 05 | Antioquia | 2006 | Centros Poblados y Rural Disperso | 165056 |
| 05 | Antioquia | 2006 | Total | 484674 |
| 05 | Antioquia | 2007 | Cabecera | 315797 |
| 05 | Antioquia | 2007 | Centros Poblados y Rural Disperso | 160695 |
| 05 | Antioquia | 2007 | Total | 476492 |
| 05 | Antioquia | 2008 | Cabecera | 312444 |

| DP | Departamento | Año | Área | Población 0–4 del área|
|---|---|---|---|---|
| 99 | Vichada | 2014 | Total | 14179 |
| 99 | Vichada | 2015 | Cabecera | 2684 |
| 99 | Vichada | 2015 | Centros Poblados y Rural Disperso | 11465 |
| 99 | Vichada | 2015 | Total | 14149 |
| 99 | Vichada | 2016 | Cabecera | 2627 |
| 99 | Vichada | 2016 | Centros Poblados y Rural Disperso | 11477 |
| 99 | Vichada | 2016 | Total | 14104 |
| 99 | Vichada | 2017 | Cabecera | 2567 |
| 99 | Vichada | 2017 | Centros Poblados y Rural Disperso | 11489 |
| 99 | Vichada | 2017 | Total | 14056 |

### Archivo DANE nacional 2018–2070

`PPED-AreaSexoEdadNac-2018-2070.xlsx` incluye `Índice`, `PPED` y `PobNacionalxáreaSexoEdad`. La hoja de datos mide A1:KW139 (139 × 309) y tiene 17 rangos combinados. Títulos y grupos de encabezado ocupan filas 1–8; encabezados de detalle están en fila 9 y registros desde fila 10. Campos iniciales: `TERRITORIO`, `AÑO`, `ÁREA GEOGRÁFICA`; luego total por sexo y edad simple, con bloques `Hombres`, `Mujeres` y `Total`. Las únicas filas de territorio de la hoja de datos son `Total Nacional`; no hay departamentos, municipios ni códigos DIVIPOLA.

Hay 119 filas de datos para los 53 años 2018–2070. Para 2018–2050 hay tres áreas (Cabecera, Centros Poblados y Rural Disperso, Total); para 2051–2070 la hoja conserva solo el área Total. En población 0–4 nacional se sumaron únicamente columnas `Total 0 años`…`Total 4 años` de fila `Total Nacional` y área `Total`. Ejemplos: 2018 = 3,805,559; 2022 = 3,803,367; 2025 = 3,688,210. Son proyecciones nacionales, no cifras de Nariño.

Filas iniciales/finales de la tabla, con año, área y suma 0–4 solo para el área Total:

| Territorio | Año | Área | Población 0–4|
|---|---|---|---|
| Total Nacional | 2018 | Cabecera | — |
| Total Nacional | 2018 | Centros Poblados y Rural Disperso | — |
| Total Nacional | 2018 | Total | 3805559 |
| Total Nacional | 2019 | Cabecera | — |
| Total Nacional | 2019 | Centros Poblados y Rural Disperso | — |
| Total Nacional | 2019 | Total | 3816056 |
| Total Nacional | 2020 | Cabecera | — |
| Total Nacional | 2020 | Centros Poblados y Rural Disperso | — |
| Total Nacional | 2020 | Total | 3845688 |
| Total Nacional | 2021 | Cabecera | — |

| Territorio | Año | Área | Población 0–4|
|---|---|---|---|
| Total Nacional | 2061 | Total | 1865357 |
| Total Nacional | 2062 | Total | 1829950 |
| Total Nacional | 2063 | Total | 1795131 |
| Total Nacional | 2064 | Total | 1760924 |
| Total Nacional | 2065 | Total | 1727341 |
| Total Nacional | 2066 | Total | 1694399 |
| Total Nacional | 2067 | Total | 1662118 |
| Total Nacional | 2068 | Total | 1630511 |
| Total Nacional | 2069 | Total | 1599596 |
| Total Nacional | 2070 | Total | 1569384 |

### Calidad estructural DANE (filas de datos, sin títulos ni encabezados)

En la hoja departamental se contaron 1.287 filas × 310 columnas: 0 celdas nulas, 0 columnas vacías y 0 filas duplicadas. Las claves `DP+DPNOM+AÑO+ÁREA GEOGRÁFICA` son únicas; hay 33 códigos/nombres territoriales, 13 años y 3 áreas. En la hoja nacional se contaron 119 filas × 309 columnas: 0 nulas, 0 columnas vacías y 0 filas duplicadas; `TERRITORIO+AÑO+ÁREA GEOGRÁFICA` no se repite. Hay 1 territorio, 53 años y tres categorías de área (con `Total` disponible todos los años, y las dos subáreas solo hasta 2050). No se detectan datos ausentes en las celdas de la tabla de datos; ello no convierte la serie en municipal ni prueba la validez demográfica de las proyecciones.

### Comparación DANE y cobertura municipal

| Característica | DCD departamental 2005–2017 | PPED nacional 2018–2070|
|---|---|---|
| Nivel geográfico | Departamental/distrital | Nacional |
| Código geográfico | DP departamental de 2 caracteres | Sin código; territorio Total Nacional |
| Municipio / DIVIPOLA municipal | No | No |
| Edad simple | Sí, hombres/mujeres/total | Sí, hombres/mujeres/total |
| Área | Cabecera, rural disperso, Total | Cabecera/rural/Total hasta 2050; Total desde 2051 |
| Nariño | Sí, como departamento DP=52 | No; solo Total Nacional |
| Población <5 | Sí a nivel departamento, suma Total_0…Total_4 | Sí a nivel nacional, suma Total 0…4 |
| Años útiles dentro de 2012–2022 | Nariño departamental 2012–2017 | Nacional 2018–2022 |
| Población municipal <5 | No | No |
| Utilidad RESPIRA | Contexto anual departamental; no clave municipal | Contexto nacional; no clave municipal |

No apareció un archivo municipal ni un archivo regional separado en la carpeta inspeccionada. El libro llamado `DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx` es departamental; el archivo 2018–2070 es nacional (no regional). La proyección municipal `codigo_municipio + año + edad simple/sexo/área` falta.

Cobertura municipal requerida 2012–2022:

| Año | Nariño en archivos DANE | Municipios de Nariño con dato | Población municipal <5 disponible|
|---|---|---|---|
| 2012 | Sí, solo departamento | 0 | NO |
| 2013 | Sí, solo departamento | 0 | NO |
| 2014 | Sí, solo departamento | 0 | NO |
| 2015 | Sí, solo departamento | 0 | NO |
| 2016 | Sí, solo departamento | 0 | NO |
| 2017 | Sí, solo departamento | 0 | NO |
| 2018 | Solo Total Nacional | 0 | NO |
| 2019 | Solo Total Nacional | 0 | NO |
| 2020 | Solo Total Nacional | 0 | NO |
| 2021 | Solo Total Nacional | 0 | NO |
| 2022 | Solo Total Nacional | 0 | NO |

No se creó `dane_poblacion_menor_5_piloto.csv`: la estructura no permite producir filas municipales sin inventar o repartir población departamental/nacional. Sí se reportó arriba el subtotal 0–4 departamental de Nariño para el DCD 2012–2017 y tres valores nacionales como ejemplos, claramente separados de cualquier cifra municipal.

La población es anual. Cuando se consiga una serie municipal adecuada, se podría enlazar por `código_municipio + año` a las semanas epidemiológicas del mismo año como contexto anual constante; no debe interpretarse como una nueva observación demográfica semanal.

## 5. Auditoría integrada de fuentes

| Fuente | Variable objetivo | Nivel geográfico | Resolución temporal | Cobertura 2012–2022 | Nariño | Estado|
|---|---|---|---|---|---|---|
| SIVIGILA evento 995 | IRA, por definir la métrica <5 | Municipal/notificación, según validación | Semanal; campo semana/año | Archivos anuales 2012–2022 presentes | Sí, sujeto a filtrar y validar códigos | Parcial: estructura disponible; grupos etarios, `num_con`, denominadores y localidad deben validarse por año. |
| IDEAM DHIME CSV | Temperatura máxima absoluta anual | Estación | Anual | 2013–2022 parcial; no 2012 | 5 estaciones; 4 con diez años completos en esta ventana | Insuficiente para semanas; copias duplicadas, mayoría preliminar. |
| IDEAM DHIME CSV | Temperatura mínima/media | Estación | Ausente | No | No en estos archivos | Ausente; solicitar serie diaria/subdiaria. |
| IDEAM DHIME CSV | Precipitación | Estación | Ausente | No | No en estos archivos | Ausente; solicitar serie diaria/subdiaria. |
| IDEAM DHIME CSV | Humedad relativa | Estación | Ausente | No | No en estos archivos | Ausente; solicitar serie diaria/subdiaria. |
| IDEAM CNE | Metadatos de estaciones, coordenadas, altitud, categoría/estado | Estación/municipio reportado | Catálogo sin observaciones temporales | No aplica | 126 estaciones del CNE, 47 etiquetas municipales | Apoyo geográfico; no es meteorología medida. |
| DANE DCD 2005–2017 | Población 0–4 | Departamental | Anual | Nariño 2012–2017 | Sí, como departamento | Apoyo contextual; no sirve como denominador municipal. |
| DANE PPED 2018–2070 | Población 0–4 | Nacional | Anual | Solo total país 2018–2022 | No a nivel Nariño | Contexto nacional, no utilizable como predictor municipal. |

### Claves de integración posibles y faltantes

- SIVIGILA: `cod_mun + año + semana`; validar si `cod_mun` representa municipio de notificación, residencia u otro nivel, conservar como texto y verificar con DIVIPOLA histórica. `fec_not` es fecha de notificación; no equivale necesariamente a fecha de ocurrencia o disponibilidad para una alerta.
- DANE municipal: no disponible. Se requiere `código DIVIPOLA municipal + año` con población 0,1,2,3,4, edad simple, desagregación que permita elegir área Total y total sexo (o sumar sexos una sola vez).
- IDEAM: los archivos DHIME solo tienen código de estación + una fecha anual y extremo térmico. Se requiere serie diaria/horaria 2012–2022 de precipitación, temperatura máxima y mínima y humedad, con unidades y banderas de calidad; asociar estación→municipio usando el CNE y criterios espaciales/altitudinales revisados.
- Una vez validadas fuentes, agregar observaciones subdiarias/diarias a semanas epidemiológicas y calcular cobertura real antes de generar una tabla municipal-semanal. No imputar ni asignar estaciones cercanas automáticamente.

## 6. Conclusiones y siguientes pasos

### SIVIGILA

Hay archivos evento 995 para todos los años 2012–2022 y campos semanales/municipales en las hojas principales. Esto basta para continuar la auditoría epidemiológica, pero no certifica todavía que el indicador `IRA menores de 5` esté definido homogéneamente ni que sea un conteo de personas únicas. El evento de morbilidad IRA se notifica colectivamente por semana según el protocolo INS 2024; numeradores/denominadores proceden de búsqueda RIPS. Confirmar definiciones y cambios por año antes de sumar o crear objetivos. [Protocolo INS IRA 2024](https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_IRA%202024.pdf).

### IDEAM

Los dos CSV no son suficientes para variables semanales. Ofrecen solo una métrica anual de temperatura máxima absoluta en cinco estaciones de Nariño, una de ellas con huecos en 2012–2022 y todas con 2012 ausente. Faltan precipitación, humedad, mínimas/medias y resolución diaria/subdiaria.

### DANE

No hay DANE municipal. DCD permite población 0–4 departamental para Nariño 2005–2017; PPED permite población 0–4 nacional 2018–2070. No hay un archivo regional independiente. Para RESPIRA se necesita el anexo municipal correspondiente, con DIVIPOLA, edad y área.

### ¿Podemos empezar el dataset integrado municipio-semana?

**No todavía.** SIVIGILA ofrece una base semanal candidata; los DHIME presentes no tienen resolución semanal ni las variables climáticas clave; DANE no dispone de población municipal. No crear predicciones, interpolaciones, imputaciones ni dataset final.

Orden recomendado:

1. Solicitar/descargar de IDEAM la serie histórica validada 2012–2022 para estaciones Nariño con precipitación diaria, temperatura mínima/máxima/medias y humedad, asegurando unidades y niveles de aprobación.
2. Solicitar/ubicar DANE municipal anual que cubra al menos 2012–2022, con edad simple y código DIVIPOLA; documentar corte/versión y cambios de municipios.
3. Validar el diccionario SIVIGILA evento 995 para cada año, los campos etarios y la definición territorial; aclarar pestañas de detalle versus agregadas y revisar anomalías de 2019 y 2021 ya documentadas en la auditoría previa.
4. Confirmar asociaciones estación-municipio por geografía, altitud y continuidad; después perfilar cobertura semanal sin rellenar faltantes.
5. Cuando las fuentes superen esas validaciones, diseñar el dataset piloto y los horizontes de 1, 2 y 3 semanas, separando fecha de ocurrencia, notificación y disponibilidad de datos.

## Reproducibilidad y alcance

El resumen CSV tiene una fila por `CodigoEstacion + Variable + Parametro`; utiliza una sola copia lógica, mantiene el código como texto y cruza los cinco códigos con CNE por identificador. No se generó piloto municipal DANE. Los dos DHIME se inspeccionaron completos; los libros DANE se examinaron estructuralmente y se calcularon únicamente las sumas 0–4 indicadas. Los SIVIGILA no se volvieron a procesar registro por registro en esta ampliación.
