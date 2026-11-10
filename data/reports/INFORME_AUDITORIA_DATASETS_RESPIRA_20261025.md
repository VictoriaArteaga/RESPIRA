# Auditoría técnica de datasets para RESPIRA

Fecha de elaboración: 2026-10-25. Inspección de solo lectura.

> Este informe describe los archivos disponibles en el directorio indicado. No entrena modelos, no transforma ni sobrescribe fuentes. Las dimensiones Excel se basan en metadatos del libro; los archivos SIVIGILA anuales se inspeccionan estructuralmente y no se agregan ni recalculan sus registros clínico-epidemiológicos.

## Resumen ejecutivo

Se encontraron catálogo nacional IDEAM (19.828 filas), catálogo Nariño `NARI_O.csv` (336 filas, 168 códigos distintos), una extracción de observaciones IDEAM/de terceros de 156.311 filas y el libro DANE nacional de población por área, sexo y edad. El libro DANE no contiene detalle municipal en esta hoja nacional; por tanto no permite estimar aquí población menor de 5 años por municipio. Se hallaron archivos SIVIGILA evento 995 para 2012–2022 en `data/SIVIGILA`. La extracción meteorológica observada cubre únicamente 25-10-2026 y no 2012–2022. No hay base para preparar todavía una serie semanal integrada.

## Inventario y auditoría

| Archivo | Tamaño | Dimensiones / estructura | Periodo | Cobertura / conclusión |
|---|---:|---|---|---|
| `Cat_logo_Nacional_de_Estaciones_del_IDEAM (1).csv` | 6,154,334 bytes | 19,828 × 19 | No aplica / inspeccionar fechas | Nacional |
| `Datos_de_Estaciones_de_IDEAM_y_de_Terceros.csv` | 35,813,886 bytes | 156,311 × 13 | 2026-10-25 04:31:00 a 2026-10-25 16:22:00 | 33 departamentos; 403 municipios; 667 estaciones; 20 sensores |
| `NARI_O.csv` | 44,574 bytes | 336 × 11 | No aplica / inspeccionar fechas | Nariño |
| `PPED-AreaSexoEdadNac-2018-2070.xlsx` | 341,148 bytes | Índice: 13×7; PPED: 12×13; PobNacionalxÁreaSexoEdad: 139×309 | 2018–2070 (nombre del libro) | Nacional por área/sexo/edad |

### Catálogo IDEAM y `NARI_O.csv`

El catálogo tiene las columnas `Codigo`, `Nombre`, `Categoria`, `Tecnologia`, `Estado`, `Departamento`, `Municipio`, `Ubicación`, `Altitud`, `LONGITUD`, `LATITUD`, `Fecha_instalacion`, `Fecha_suspension`, `Area Operativa`, `Corriente`, `Area Hidrografica`, `Zona Hidrografica`, `Subzona hidrografica`, `Entidad`. CSV UTF-8 con BOM, autodetección de separador (coma), 19 columnas; tipos inferidos: códigos enteros, coordenadas flotantes, altitud entera y resto texto. Las columnas son etiquetas observadas del archivo; salvo categoría/estado geográfico, la semántica instrumental y los cambios de catálogo requieren diccionario oficial.

- Catálogo nacional: 19,828 filas, 9,914 códigos distintos; estados: {'Activa': 11310, 'Suspendida': 7786, 'En Mantenimiento': 732}.
- Nariño: 336 filas; 168 códigos distintos; 47 etiquetas municipales. `168` filas son repeticiones de código, por lo que no deben contarse como estaciones únicas sin resolverlas.
- Categorías Nariño (filas): {'Pluviométrica': 128, 'Climatológica Principal': 56, 'Limnigráfica': 52, 'Climatológica Ordinaria': 40, 'Limnimétrica': 20, 'Meteorologica Marina': 10, 'Meteorológica Especial': 10, 'Pluviográfica': 6, 'Sinóptica Principal': 4, 'Agrometeorológica': 4, 'Sinóptica Secundaria': 2, 'Radio Sonda': 2, 'Ambiental': 2}.
- Estados Nariño: {'Activa': 218, 'Suspendida': 104, 'En Mantenimiento': 14}.
- `NARI_O.csv` repite exactamente el subconjunto departamental del catálogo: no tiene fecha de observación, valor medido ni campos de sensor/unidad. No es evidencia de una serie temporal ni de medición activa.

Estaciones Nariño con categoría climatológica (candidatas, por categoría solamente; no confirma sensor ni continuidad):

| Código | Estación | Categoría | Estado | Municipio | Altitud m |
|---|---|---|---|---|---:|
| 5204500108 | APONTE - CUENCA ALTA RIO PASTO - AUT   [5204500108] | Climatológica Principal | Suspendida | El Tablón | 2095 |
| 5205500123 | LAS IGLESIAS  - AUT [5205500123] | Climatológica Principal | Activa | Pasto | 2973 |
| 52055210 | BOTANA - AUT [52055210] | Climatológica Principal | Activa | Pasto | 2820 |
| 51025030 | CANDELILLAS  [51025030] | Climatológica Ordinaria | Suspendida | Tumaco | 20 |
| 52055120 | PIEDRAS TANGUA  [52055120] | Climatológica Principal | Activa | Tangua | 3087 |
| 52055200 | FUNES [52055200] | Climatológica Ordinaria | Activa | Funes | 2181 |
| 52040050 | APONTE [52040050] | Climatológica Principal | Activa | El Tablón | 1800 |
| 52055090 | SINDAGUA [52055090] | Climatológica Principal | Activa | Tangua | 2800 |
| 52055220 | EL PARAISO - AUT [52055220] | Climatológica Principal | Activa | Túquerres | 3033 |
| 52045040 | TAMINANGO [52045040] | Climatológica Ordinaria | Activa | Taminango | 1875 |
| 52035040 | VIENTO LIBRE - AUT [52035040] | Climatológica Ordinaria | Activa | Taminango | 1400 |
| 52055170 | LA JOSEFINA - AUT [52055170] | Climatológica Principal | Activa | Contadero | 2450 |
| 5102500128 | RESERVA NATURAL LA PLANADA - AUT   [5102500128] | Climatológica Principal | Activa | Ricaurte | 1835 |
| 52065020 | BARBACOAS [52065020] | Climatológica Principal | Activa | Barbacoas | 32 |
| 52045070 | WILQUIPAMBA [52045070] | Climatológica Ordinaria | Activa | Pasto | 2850 |
| 52055502 | SANDONA  - AUT  [52055502] | Climatológica Principal | Activa | Sandoná | 1838 |
| 52050060 | RIO BOBO [52050060] | Climatológica Principal | Activa | Pasto | 364 |
| 51025070 | RICAURTE - AUT [51025070] | Climatológica Principal | Suspendida | Ricaurte | 1210 |
| 51025020 | RICAURTE [51025020] | Climatológica Principal | Suspendida | Ricaurte | 1181 |
| 52055100 | VILLA ROSA [52055100] | Climatológica Ordinaria | Suspendida | Sapuyes | 3000 |
| 52055190 | CASANARE  - AUT  [52055190] | Climatológica Principal | Activa | Pasto | 2941 |
| 51025060 | BIOTOPO - AUT [51025060] | Climatológica Principal | En Mantenimiento | Barbacoas | 512 |
| 52055060 | TANAMA [52055060] | Climatológica Ordinaria | Activa | Samaniego | 1500 |
| 52045080 | UNIVERSIDAD DE NARINO  - AUT [52045080] | Climatológica Ordinaria | Activa | Pasto | 2626 |
| 47015080 | MONOPAMBA [47015080] | Climatológica Ordinaria | Activa | Puerres | 1776 |
| 52055180 | PIEDRAS  [52055180] | Climatológica Principal | Activa | Tangua | 3178 |
| 51025090 | GRANJA EL MIRA - - AUT [51025090] | Climatológica Principal | En Mantenimiento | Tumaco | 16 |
| 52055130 | CAMPANERO SAN  [52055130] | Climatológica Principal | Activa | Pasto | 2872 |
| 51025080 | ALTAQUER - AUT [51025080] | Climatológica Principal | Activa | Barbacoas | 1182 |
| 52055150 | CERRO PARAMO  - AUT [52055150] | Climatológica Principal | Activa | Puerres | 3585 |
| 52045090 | EL COMÚN [52045090] | Climatológica Ordinaria | Activa | Pupiales | 3141 |
| 5205500767 | CONSACÁ - AUT [5205500767] | Climatológica Ordinaria | Activa | Consacá | 1948 |
| 52055110 | CHIMAYOY [52055110] | Climatológica Ordinaria | Suspendida | Pasto | 2745 |
| 52045030 | SAN BERNARDO [52045030] | Climatológica Ordinaria | Activa | San Bernardo | 2190 |
| 51035020 | CCCP DL PACIFICO [51035020] | Climatológica Principal | Activa | Tumaco | 1 |
| 52055030 | BOMBONÁ [52055030] | Climatológica Ordinaria | En Mantenimiento | Consacá | 1493 |
| 52035501 | EL SAUCE  - AUT  [52035501] | Climatológica Principal | Activa | La Unión | 1609 |
| 47015100 | EL ENCANO - AUT [47015100] | Climatológica Principal | Activa | Pasto | 2830 |
| 52050090 | IMUES [52050090] | Climatológica Principal | Activa | Imués | 2550 |
| 52055160 | VOLCAN CHILES  - AUT [52055160] | Climatológica Principal | En Mantenimiento | Cumbal | 442 |
| 52050080 | TANGUA [52050080] | Climatológica Principal | Activa | Tangua | 2420 |
| 52055140 | COBANEGRA  - AUT  [52055140] | Climatológica Principal | Activa | Pasto | 3390 |
| 52055501 | OSPINA PEREZ  - AUT  [52055501] | Climatológica Ordinaria | Activa | Consacá | 1632 |
| 5204500752 | EL TAMBO (GIA) - AUT [5204500752] | Climatológica Ordinaria | Activa | El Tambo | 2178 |
| 5204500769 | BUESACO - AUT [5204500769] | Climatológica Ordinaria | Activa | Buesaco | 1919 |
| 52055050 | SINDAMANOY  [52055050] | Climatológica Ordinaria | Suspendida | Pasto | 2527 |
| 52045050 | COL MARIDIAZ  [52045050] | Climatológica Ordinaria | Suspendida | Pasto | 2380 |
| 52055070 | OSPINA PEREZ  [52055070] | Climatológica Ordinaria | Activa | Consacá | 1700 |

Candidatas de precipitación por categoría (`Pluviométrica`/`Pluviográfica`), no garantía de disponibilidad: 
52030020 PRESA HIDROMAYO [52030020] (Colón (Génova), Suspendida), 51030020 COCO EL [51030020] (Tumaco, Activa), 51020030 CHARCO EL  [51020030] (Ipiales, Suspendida), 52050190 SANTA ROSA POTOSI [52050190] (Potosí, Activa), 52040110 PASANTO [52040110] (Pasto, Suspendida), 52050100 GUALMATAN [52050100] (Gualmatán, Activa), 53010020 MOSQUERA [53010020] (Mosquera, Activa), 52070020 RICAURTE [52070020] (Magüí (Payán), Suspendida), 52040140 UNIV NARINO  [52040140] (Pasto, Suspendida), 52050150 EDIFICIO TUQUERRES  [52050150] (Túquerres, Suspendida), 52080020 POLICARPA [52080020] (El Rosario, Suspendida), 52090010 SALAHONDA [52090010] (Francisco Pizarro (Salahonda), Activa), 52070010 MAGUI [52070010] (Magüí (Payán), Activa), 52050070 TUQUERRES [52050070] (Túquerres, Suspendida), 52040070 NARINO [52040070] (Nariño, Activa), 52030060 HIDROMAYO CAMP [52030060] (Colón (Génova), Activa), 52050160 CAMP PILCUAN  [52050160] (Imués, Suspendida), 52050030 SAMANIEGO [52050030] (Samaniego, Suspendida), 52040150 COL MARIDIAZ  [52040150] (Pasto, Suspendida), 47010040 CHALET GUAMUES [47010040] (Pasto, Suspendida), 51030010 CAMP LA YE  [51030010] (Tumaco, Suspendida), 52030030 UNION LA [52030030] (La Unión, Activa), 52040060 ROSAL DEL MONTE [52040060] (Buesaco, Activa), 52050120 PUERRES [52050120] (Puerres, Activa), 52090020 REMOLINO GRANDE [52090020] (Roberto Payán (San José), Activa), 52050170 AGROYACO [52050170] (El Tambo, Suspendida), 52010140 GUASCA LA [52010140] (Policarpa, Activa), 52040100 HOTEL SINDAMANOY  [52040100] (Pasto, Suspendida), 52030110 UNION LA  [52030110] (La Unión, Activa), 53020010 CHARCO EL [53020010] (El Charco, Activa)
. El catálogo no contiene una variable observada, frecuencia, medición individual ni fechas de cobertura histórica; estaciones activas tampoco garantizan cobertura histórica.

### CSV de observaciones IDEAM/de terceros

Datos_de_Estaciones_de_IDEAM_y_de_Terceros.csv: 156311 x 13; columnas ['CodigoEstacion', 'CodigoSensor', 'FechaObservacion', 'ValorObservado', 'NombreEstacion', 'Departamento', 'Municipio', 'ZonaHidrografica', 'Latitud', 'Longitud', 'DescripcionSensor', 'UnidadMedida', 'Entidad']. Periodo 2026-10-25 04:31:00 a 2026-10-25 16:22:00; marcas 712. Estaciones 667; sensores 21; descripciones 20; celdas vacias 1030. Filas Nariño 6015; estaciones Nariño 33. Solo corte de 25-10-2026; no sirve para serie 2012-2022.

Principales descripciones de sensor:

- Precipitación acumulada 10 minutos: 59,931
- Velocidad del viento cada 10 minutos: 20,740
- Dirección del viento cada 10 minutos: 20,626
- Temperatura del suelo a 50 cm: 13,616
- Humedad relativa del suelo a 50 cm horaria: 12,659
- Temperatura del aire a 2 metros: 4,202
- Humedad relativa del aire a 2 metros horaria: 4,167
- Presión atmosférica horaria: 3,777
- Temperatura mínima del Aire a 2 metros: 3,465
- Temperatura máxima del Aire a 2 metros: 3,429
- Nivel horario por sensor automático: 2,645
- Nivel mínimo horario: 1,743
- Nivel máximo horario: 1,720
- Evaporación total horaria: 1,418
- Humedad relativa del suelo a 30 cm horaria: 679
- Temperatura del suelo a 30 cm: 533
- Temperatura del suelo a 10 cm: 375
- Nivel del rio a las 600 y 1800 po limnímetro: 53
- Temperatura seca de las 700, 1300 y 1800: 10
- Temperatura mínima diaria: 8

Cobertura del corte en Nariño por descripción (cantidad de estaciones; no periodo histórico):

- Precipitación acumulada 10 minutos: 28 estaciones
- Dirección del viento cada 10 minutos: 19 estaciones
- Velocidad del viento cada 10 minutos: 19 estaciones
- Temperatura mínima del Aire a 2 metros: 18 estaciones
- Temperatura del aire a 2 metros: 18 estaciones
- Humedad relativa del aire a 2 metros horaria: 18 estaciones
- Temperatura máxima del Aire a 2 metros: 18 estaciones
- Presión atmosférica horaria: 17 estaciones
- Nivel máximo horario: 10 estaciones
- Nivel horario por sensor automático: 10 estaciones
- Nivel mínimo horario: 10 estaciones
- Evaporación total horaria: 9 estaciones
- Nivel del rio a las 600 y 1800 po limnímetro: 6 estaciones
- Temperatura del suelo a 10 cm: 5 estaciones
- Temperatura del suelo a 30 cm: 5 estaciones
- Humedad relativa del suelo a 50 cm horaria: 4 estaciones
- Humedad relativa del suelo a 30 cm horaria: 4 estaciones
- Temperatura del suelo a 50 cm: 4 estaciones

Estaciones Nariño con sensores útiles presentes en este corte (precipitación/temperatura/humedad):

- 47015100 — EL ENCANO - AUT [47015100]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 47017110 — MONOPAMBA  - AUT [47017110]: Precipitación acumulada 10 minutos
- 51020011 — PIEDRANCHA - AUT [51020011]: Precipitación acumulada 10 minutos
- 51025080 — ALTAQUER - AUT [51025080]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 51025090 — GRANJA EL MIRA - - AUT [51025090]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 51027060 — SAN JUAN MIRA - AUT [51027060]: Precipitación acumulada 10 minutos
- 51035020 — CCCP DL PACIFICO [51035020]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 51039010 — TUMACO - AUT [51039010]: Precipitación acumulada 10 minutos
- 52017001 — PUERTO NUEVO PATIA - AUT [52017001]: Precipitación acumulada 10 minutos
- 52035040 — VIENTO LIBRE - AUT [52035040]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52040050 — APONTE [52040050]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52045080 — UNIVERSIDAD DE NARINO  - AUT [52045080]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52050060 — RIO BOBO [52050060]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52050080 — TANGUA [52050080]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52050090 — IMUES [52050090]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52055090 — SINDAGUA [52055090]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52055150 — CERRO PARAMO  - AUT [52055150]: Precipitación acumulada 10 minutos
- 52055160 — VOLCAN CHILES  - AUT [52055160]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52055170 — LA JOSEFINA - AUT [52055170]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52055210 — BOTANA - AUT [52055210]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52055220 — EL PARAISO - AUT [52055220]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52055230 — AEROPUERTO SAN LUIS - AUT [52055230]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52057050 — SAN PEDRO  - AUT [52057050]: Precipitación acumulada 10 minutos
- 52057100 — RUMICHACA - AUT [52057100]: Precipitación acumulada 10 minutos
- 52065020 — BARBACOAS [52065020]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros
- 52077010 — PUENTE PUSMEO - AUT [52077010]: Precipitación acumulada 10 minutos
- 5204700100 — PUENTE LOS DOLORES - AUT  [5204700100]: Precipitación acumulada 10 minutos
- 5205500123 — LAS IGLESIAS  - AUT [5205500123]: Humedad relativa del aire a 2 metros horaria, Precipitación acumulada 10 minutos, Temperatura del aire a 2 metros, Temperatura máxima del Aire a 2 metros, Temperatura mínima del Aire a 2 metros

### Población DANE

El libro `PPED-AreaSexoEdadNac-2018-2070.xlsx` contiene hojas de índice y presentación, y una hoja de serie **Nacional** por área, sexo y edad. En la tabla, las filas son territorio × año × área; las edades simples están desglosadas por sexo y existe bloque `Total` por edad. Para población 0–4 nacional debe usarse exclusivamente el bloque Total 0, 1, 2, 3, 4; alternativamente sumar ambos sexos, nunca ambos y Total a la vez. “Cabecera”, “Centros Poblados y Rural Disperso” y “Total” son categorías no aditivas entre sí: usar solo Total para población nacional.

La hoja contiene filas de datos para `Total Nacional` por área; no aparecen departamentos ni municipios entre los registros de datos. No incluye municipios ni códigos DIVIPOLA; por tanto no es posible calcular de forma fiable población municipal menor de cinco años para Nariño en 2018, 2022 o 2025. Hace falta el anexo municipal DANE por área, sexo y edad simple del periodo correspondiente. Aunque el archivo se titula 2018–2070, validar dentro de la hoja y metadatos las filas/años disponibles antes de uso. La nota de actualización indica 18-07-2025.

### SIVIGILA evento 995

- `Datos_2012_995.xlsx` (92,264,928 bytes): hoja 995 52, 144,299 filas × 77, encabezados fila 1, 77 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, demanda, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, hospital_1, hospital_2, hospital_3, hospital_4…`; hoja Base Recibida, 144,299 filas × 77, encabezados fila 1, 77 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, demanda, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2013_995.xlsx` (73,873,471 bytes): hoja Hoja1, 187,955 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2014_995.xlsx` (63,497,745 bytes): hoja Hoja1, 178,567 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2015_995.xlsx` (65,648,298 bytes): hoja Hoja1, 184,986 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2016_995.xlsx` (81,232,572 bytes): hoja Hoja1, 231,882 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2017_995.xlsx` (84,909,437 bytes): hoja EVENTO 995, 238,173 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2018_995.xlsx` (88,692,007 bytes): hoja Hoja1, 240,895 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2019_995.xlsx` (119,179,432 bytes): hoja Hoja1, 55,113 filas × 10, encabezados fila 3, 10 campos: `semana, cod_eve, nom_eve, cod_dep, ndep_notif, cod_mun, nmun_notif, Suma de tot_irag, Suma de tot_irauci, Suma de tot_iraext`; hoja Final, 245,200 filas × 85, encabezados fila 1, 85 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_dep, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3…`
- `Datos_2020_995.xlsx` (77,100,018 bytes): hoja 995_2020_Depurada, 215,730 filas × 84, encabezados fila 1, 84 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2021_995.xlsx` (77,043,344 bytes): hoja ACUMULADO, 1,048,576 filas × 85, encabezados fila 2, 85 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`
- `Datos_2022_995.xlsx` (85,118,826 bytes): hoja 995, 235,740 filas × 83, encabezados fila 1, 83 campos: `cod_eve, fec_not, semana, año, cod_pre, cod_sub, cod_mun, num_con, grupoh_1, grupoh_2, grupoh_3, grupoh_4, grupoh_5, grupoh_6, grupoh_7, tot_irag, hospital_1, hospital_2, hospital_3, hospital_4…`

2012 contiene hojas `995 52` y `Base Recibida`; 2013–2018 tienen una hoja principal con nombres variables; 2019 incluye `Hoja1` (resumen agregado) y `Final` (detalle); 2020 usa `995_2020_Depurada`; 2021 `ACUMULADO`; 2022 `995`. Se detectó encabezado en fila 2 para 2021 (fila 1 tiene rótulos parciales), y la hoja alcanza exactamente el límite de 1.048.576 filas de Excel: revisar si está truncada. Una fila de muestra presenta `fec_not=2022-01-01`, `año=2021`, `semana=52`, lo que amerita validar calendario/cierre y fecha de notificación. En `2019`, no mezclar `Hoja1` agregada con `Final` detallada. En muestra se observan `cod_eve`, `fec_not`, `semana`, `año`, `cod_pre`, `cod_sub`, `cod_mun`, `num_con`, `demanda`, `grupoh_*`, `hospital_*`, `tot_irag` (variación de campos entre años). `cod_mun` parece código DIVIPOLA de cinco dígitos en la hoja Base Recibida, pero debe verificarse por diccionario y normalizarse como texto con ceros iniciales; `cod_pre` parece prestador/UPGD, no municipio de residencia. No se asigna significado clínico a cada sufijo por nombre solamente. Según protocolo INS 2024, morbilidad IRA evento 995 es notificación colectiva semanal, con numeradores y denominadores basados en búsqueda RIPS; no equivale a personas únicas ni casos individuales. Verificar definición histórica por año, fecha efectiva y tipo de población antes de calcular menores de 5. No se agregaron registros ni se auditaron valores/duplicados de las 11 bases; ese análisis requerirá reglas de datos y validación de columnas.

## Compatibilidad geográfica y temporal

No se construyó una matriz municipal completa porque el libro DANE disponible es nacional y el catálogo meteorológico no codifica municipios DIVIPOLA. Los archivos SIVIGILA sí traen `cod_mun` y `cod_pre`, pero su significado y la localidad notificada/residencia/ocurrencia requieren diccionario INS y validación. La unión por nombre aproximado no es aceptable. Usar DIVIPOLA como texto y una tabla oficial vigente/histórica para cambios territoriales. IDEAM presenta municipio como texto; resolverlo mediante catálogo y código geográfico validado antes de unir.

| Fuente | Periodo comprobado | Granularidad | Aporta a dataset semanal 2012–2022 |
|---|---|---|---|
| IDEAM catálogo / `NARI_O.csv` | Fechas de instalación/suspensión, no observaciones | Estación | Parcial: mapa de estaciones potenciales; cobertura de variables no comprobada |
| Observaciones IDEAM/terceros | 25-10-2026 | Estación-sensor-observación (intervalos subdiarios) | No para entrenamiento histórico 2012–2022 |
| DANE | Proyección 2018–2070 declarada; hoja nacional | Año × área × sexo × edad | No por municipio con archivo presente |
| SIVIGILA 995 | Archivos anuales 2012–2022; campos fec_not/semana | Agregado colectivo notificante/municipio según validación | Potencialmente sí, tras diccionario, población etaria y calidad |

## Evaluación para RESPIRA

| Variable candidata | Estado | Observación |
|---|---|---|
| Año/semana epidemiológica | Parcialmente disponible | `semana`, `año` en SIVIGILA; validar calendario epidemiológico, semanas faltantes y cambios de formato. |
| Municipio DIVIPOLA | Pendiente de validar | `cod_mun` en SIVIGILA; catálogo IDEAM da nombres; anexo municipal DANE ausente. |
| IRA <5 años | Pendiente de validar | Evento colectivo; significados de grupos edad y tipo de servicio/denominador deben verificarse por año. |
| Temperatura máxima/mínima, precipitación, humedad | Parcial/ausente históricamente | Sensor descriptions existen en snapshot 2026, pero no hay historia 2012–2022. |
| Población municipal <5 | Ausente en archivo presente | Libro DANE nacional solamente. |
| Variables semanales derivadas | Pendiente | Requiere originales de observación multianuales, agregación temporal validada y reglas de datos faltantes. |

Horizontes futuros: para semana objetivo `t+h`, definir por separado un objetivo a 1, 2 y 3 semanas usando la métrica IRA validada en semana `t+h`; comparar alerta de umbral o cambio relativo contra una línea base, sin mezclar consultas, hospitalizaciones, UCI y muertes. Cada predictor debe limitarse a información disponible al momento de emitir alerta. La fecha de notificación (`fec_not`) no necesariamente es fecha de ocurrencia; el retraso de reporte debe modelarse/medirse.

2012–2022 podría permitir una prueba histórica epidemiológica exploratoria si se obtienen datos meteorológicos de ese periodo y se resuelven cambios de formulario/definición, completitud y geografía. No se puede afirmar suficiencia predictiva con los archivos actuales.

## Riesgos y pendientes

- Repetición de 168 códigos en las 336 filas Nariño: revisar duplicados de catálogo antes de contar estaciones y distinguir múltiples sensores/versiones o registros repetidos.
- `NARI_O.csv` no observa tiempo meteorológico; no confundir catálogos con datos medidos.
- Los datos observados disponibles son un corte contemporáneo de horas de 2026, por lo que no resuelven retroalimentación temporal histórica, consistencia ni completitud anual.
- No se identificó DIVIPOLA en DANE porque el detalle municipal no está en el libro actual; código numérico puede perder cero inicial si se trata como entero.
- Distintas estructuras de pestañas/campos en SIVIGILA por año; el segundo tab Base Recibida puede diferir de la pestaña publicada. Debe definirse cuál es el extracto autoritativo.
- El catálogo no permite validar físicamente coordenadas ni altitud sin límites oficiales y referencias; no se han supuesto rangos como evidencia de invalidez.
- Para estaciones cercanas, la asociación municipal requiere distancia, altitud, barreras topográficas y cobertura. No se propone una asignación automática.
- Riesgo de fuga temporal: no usar observaciones/denominadores que no estarían disponibles al emitir alerta; separar fecha de ocurrencia, notificación y disponibilidad.

## Próximos pasos priorizados

1. Solicitar/ubicar la serie IDEAM histórica diaria u horaria 2012–2022 con códigos de estación, fecha, variable, unidad y flags de calidad; verificar las candidatas climatológicas y pluviométricas de Nariño.
2. Obtener el archivo DANE municipal por área, sexo y edad simple y validar cobertura por municipio/año; sumar edades 0–4 únicamente en área Total y ambos sexos o bloque Total.
3. Conseguir diccionario de datos/formatos SIVIGILA evento 995 de cada año y confirmar semántica de `cod_mun`, `cod_pre`, grupos de edad, `demanda`/`num_con` y la pestaña analítica autorizada.
4. Obtener DIVIPOLA oficial/histórica y definir claves canónicas en texto para cada fuente.
5. Luego de validar definiciones, perfilar duplicados, vacíos, semanas y completitud estación-variable-año por bloques; construir matriz municipal de cobertura con asociaciones de estaciones revisadas.
6. Solo después diseñar objetivos de horizonte 1–3 semanas y esquema de validación temporal; no entrenar aún.

## Documentación externa consultada (2026-10-25)

- DANE, Proyecciones de población 2018–2070 / actualización de 18-07-2025: https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion
- DANE, DIVIPOLA: https://www.dane.gov.co/index.php/sistema-estadistico-nacional-sen/normas-y-estandares/nomenclaturas-y-clasificaciones/nomenclaturas/codificacion-de-la-division-politica-administrativa-de-colombia-divipola
- INS, Protocolo IRA 2024 (incluye evento 995, notificación colectiva semanal y numeradores/denominadores RIPS): https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_IRA%202024.pdf
- IDEAM: no se consultó documentación de definición instrumental/estándar de los campos del catálogo en esta inspección; significado de sensores por categoría queda pendiente de confirmar.

## Reproducibilidad

Script de auditoría: `scripts/auditar_datasets_respira.py`. Uso: `python scripts/auditar_datasets_respira.py --data "<carpeta data>" --out reports`. Solo lee CSV/XLSX y escribe un informe con nueva fecha; no modifica los archivos fuente. El análisis SIVIGILA actual es estructural, no una validación exhaustiva registro por registro.
