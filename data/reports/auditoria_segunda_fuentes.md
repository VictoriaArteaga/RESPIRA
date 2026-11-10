# Segunda auditoría de fuentes oficiales para RESPIRA

**Fecha:** 25 de octubre de 2026  
**Alcance:** inspección local, de solo lectura, de dos libros municipales DANE y de las extracciones IDEAM disponibles. No se descargaron fuentes, no se modificaron archivos originales, no se integró SIVIGILA ni se creó el dataset final.

## 1. Resumen ejecutivo

La segunda auditoría resuelve la limitación demográfica anterior: los dos libros municipales DANE permiten calcular de forma reproducible la población de 0 a 4 años para los 64 municipios de Nariño en cada año de 2012 a 2022 (704 municipio-año). En ambos libros se verificó la consistencia del total de edades 0–4 frente a hombres + mujeres, sin claves duplicadas ni datos nulos en los campos usados.

Las extracciones locales de IDEAM incluyen precipitación y temperaturas diarias, además de muchas otras variables. En el subconjunto Nariño se auditaron 414 archivos de estación, de 207,495,999 bytes en total. La disponibilidad es desigual: de las 99 estaciones con precipitación, 41 tienen al menos 80% de días observados en cada uno de los once años 2012–2022; para máximas, mínimas y medias de temperatura, nueve de 22 estaciones cumplen ese mismo umbral. El umbral de 80% es una regla descriptiva para esta auditoría, no un estándar oficial ni una validación climatológica.

Los archivos de observación no contienen unidades, banderas de calidad o aprobación. Algunos códigos de variable adicionales requieren confirmación de IDEAM. Por tanto, **DANE queda apto con condiciones documentadas; las series diarias de precipitación y temperatura son aptas con limitaciones para una etapa de selección y validación, pero todavía no para una integración automática final**. La humedad relativa es pendiente de confirmación semántica. Se recomienda avanzar a diseño de integración y validación por estación, sin declarar aún una fuente meteorológica municipal completa.

## 2. Inventario local

| Fuente local | Inventario observado | Resultado |
|---|---:|---|
| `PrecipitacionNacionalDiaria` | 4,450 `.data` (977,066,129 bytes) | Extracción legible; no se encontró ZIP original local |
| `TemperaturaNacionalDiaria` | 2,562 `.data` (809,077,913 bytes) | Extracción legible; no se encontró ZIP original local |
| `MetereologiaNacionalDiaria` | 6,426 `.data` (2,839,574,268 bytes) | Extracción legible; no se encontró ZIP original local |
| DANE municipal 2005–2017 | `DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx` (55,969,926 bytes) | Leído y auditado |
| DANE municipal 2018–2042 | `PPED-AreaSexoEdadMun-2018-2042_VP.xlsx` (131,609,579 bytes) | Leído y auditado |
| Catálogo IDEAM CSV nacional | `Cat_logo_Nacional_de_Estaciones_del_IDEAM (1).csv` | Leído para cruce por código |
| CNE IDEAM `.xls` | Catálogo nacional, hoja `CNE` | Disponible como referencia separada; no se fusionó con el CSV nacional |

Los tres ZIP de IDEAM indicados como referencia por el proyecto no estaban disponibles localmente; sí estaban sus directorios extraídos. Sin los ZIP ni hashes no es posible demostrar que la extracción coincide byte por byte con la descarga oficial, ni determinar la fecha/version exacta de adquisición. Referencias de origen: [precipitación](https://bart.ideam.gov.co/PQRS/AQTSUtils/PrecipitacionNacionalDiaria.zip), [temperatura](https://bart.ideam.gov.co/PQRS/AQTSUtils/TemperaturaNacionalDiaria.zip), [meteorología](https://bart.ideam.gov.co/PQRS/AQTSUtils/MetereologiaNacionalDiaria.zip), [DHIME](https://ideam.gov.co/dhime) y [Catálogo Nacional de Estaciones IDEAM](https://ideam.gov.co/transparencia/datos-abiertos/seccion-de-datos-abiertos/catalogo-nacional-de-estaciones-del-ideam). No se hizo ninguna descarga.

## 3. Auditoría DANE

### 3.1 Serie municipal 2005–2017

- Hoja: `NuevaMpal`; dimensión de hoja A6:JG43770 (43,770 filas × 267 columnas, incluidas filas de título y encabezado).
- Encabezado real en fila 12; registros desde fila 13. Hay 43,758 filas, correspondientes a 1,122 códigos municipales × 13 años × tres ámbitos territoriales.
- Años observados: 2005–2017. Ámbitos: `Cabecera Municipal`, `Centros Poblados y Rural Disperso` y `Total`.
- En este archivo, `DP` es código de departamento, `DPNOM` nombre del departamento, `DPMP` nombre del municipio y `MPIO` código municipal de cinco dígitos. Para Nariño, `DP=52`.
- Hay edades simples 0–84 y grupo 85 y más por sexo, además de totales por sexo y total general. Las edades 0, 1, 2, 3 y 4 están disponibles separadamente.
- Cobertura Nariño: 64 códigos municipales para cada año 2005–2017. En particular, 64 × 6 = 384 municipio-año en 2012–2017.
- En el barrido de las 267 columnas no hubo filas idénticas ni claves repetidas `(código, año, área)`. Tampoco hubo nulos en código, año, área o total de población 0–4. El total 0–4 coincidió con la suma de hombres 0–4 y mujeres 0–4 en todas las filas.

### 3.2 Serie municipal 2018–2042

- Hojas: `Índice`, `PPED` y `PobMunicipalxáreaSexoEdad`. La hoja de datos mide A1:KZ84245 (84,245 × 312); títulos en filas 3, 5 y 7, encabezado agrupado en fila 8 y encabezado de campo en fila 9; datos desde fila 10.
- La hoja `PPED` señala actualización al 30 de julio de 2025. La página oficial de proyecciones DANE publica las series municipales 2005–2017 y 2018–2042 y registra actualización el 8 de agosto de 2025; la serie está en el contexto de las proyecciones basadas en el CNPV 2018 y actualizaciones posteriores ([DANE, proyecciones de población](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion)).
- Años observados: 2018–2042. Hay 84,225 registros, 1,123 códigos municipales × 25 años × tres ámbitos territoriales. Los ámbitos tienen los mismos rótulos que el archivo anterior.
- En este libro, `DPMP` es el nombre de municipio y `MPIO` es el código municipal. Esta disposición difiere de la serie 2005–2017: no debe asignarse significado por posición ni reutilizar el nombre del campo sin armonizarlo.
- Se encuentran edades simples, desagregadas por hombres y mujeres, con totales; hay grupo abierto para las edades mayores. Los campos de 0 a 4 años están separados.
- Cobertura Nariño: 64 códigos para cada año de 2018–2042; 64 × 5 = 320 municipio-año para 2018–2022.
- En el barrido de las 312 columnas no hubo filas idénticas ni claves repetidas `(código, año, área)`, ni nulos en código, año, área o población total 0–4. En todas las filas, el total 0–4 igualó hombres + mujeres de esas edades.

### 3.3 Cálculo recomendado y continuidad

Usar una sola fila por municipio-año con ámbito `Total`, y sumar únicamente los campos de **población total** para las edades simples 0, 1, 2, 3 y 4. Alternativamente, sumar hombres y mujeres dentro de cada edad, sin sumar además los campos de total. No sumar `Cabecera Municipal` y `Centros Poblados y Rural Disperso` junto con `Total`. Conservar los códigos municipales como texto de cinco posiciones y registrar el libro/versión de origen.

El empalme entrega los 64 municipios en todos los años 2012–2022: **704 de 704 municipio-año, sin vacíos observados**. La serie 2005–2017 y la 2018–2042 son libros distintos, con distinto orden/uso de campos territoriales y sin años superpuestos; conservar la procedencia al armonizar. Los conteos son proyecciones anuales y no observaciones semanales: la población anual puede asociarse a semanas del mismo municipio-año, pero no debe describirse como estimación semanal.

## 4. Auditoría IDEAM

### 4.1 Formato, variables y cruce de estaciones

Se inspeccionaron los 13,438 archivos de las tres carpetas nacionales; la búsqueda local no encontró ZIP. Los archivos son texto `.data` con dos columnas (`Fecha|Valor`) y nombre con etiqueta/código, por ejemplo `<variable>@<código>.data`. La fecha aparece como marca de tiempo (`AAAA-MM-DD HH:MM:SS`); no se encontraron columnas de unidad, indicador de calidad, aprobación o estado preliminar/definitivo. Para el análisis territorial se procesaron los 414 archivos enlazados a Nariño por código con el CSV nacional de estaciones.

El CSV de catálogo tiene 19,828 filas pero 9,914 códigos normalizados: cada código está representado por dos filas idénticas; no se detectaron conflictos de municipio, departamento o coordenadas para esos códigos. En Nariño hay 336 filas y 168 códigos, también con duplicación exacta. Los códigos del catálogo pueden tener ceros iniciales; se normalizó quitándolos a la izquierda para buscar la coincidencia con el código del nombre de archivo, sin unir por parecido de nombres. El CNE `.xls` es otra edición/alcance: tiene 4,522 estaciones y 126 registros etiquetados Nariño en 47 nombres municipales. No se mezclaron estos catálogos; las diferencias de alcance/versionado requieren resolución antes de fijar metadatos definitivos. Las coordenadas y altitudes se deben tomar del catálogo tras resolver la edición vigente, no inferirse por proximidad.

El cruce de Nariño permitió asignar código, nombre y municipio del CSV nacional. Los directorios no aportan sus propios metadatos geográficos. El archivo resumen por estación-variable documenta nombre, municipio, categoría/estado catalogado, rango observado y controles por archivo. Los conteos por municipio no implican que exista una estación para cada uno de los 64 municipios.

### 4.2 Inventario IDEAM de Nariño

| Etiqueta original | Archivos/estaciones | Filas históricas | Rango del subconjunto | Lectura semántica / unidad según documentación |
|---|---:|---:|---|---|
| `PTPM_CON_INTER` | 99 | 1,234,155 | 1924-01-01–2026-08-12 | Precipitación diaria; manual identifica `PTPM_CON`, mm, día pluviométrico |
| `TSSM_CON` | 22 | 684,096 | En archivos desde 1979; hasta 2026 | Temperatura seca en observaciones de 07, 13 y 18/19 h; °C, no es una única observación diaria |
| `TSSM_MEDIA_D` | 22 | 252,814 | 1976-05-01–2026-08-09 | Temperatura media diaria derivada; °C |
| `TSSM_MX_D` | 22 | 218,234 | 1979-01-01–2026-08-09 | Temperatura máxima diaria derivada; °C |
| `TSSM_MN_D` | 22 | 218,234 | 1979-01-01–2026-08-09 | Temperatura mínima diaria derivada; °C |
| `HR_CAL_MEDIA_D` | 23 | 241,084 | 1976-05-01–2026-07-31 | Código sugiere humedad relativa media, pero no se confirmó significado ni unidad en el glosario consultado |
| `FA_CON`, `NB_CON`, `BSHG_TT_D`, `EVTE_CON`, `RCAM_CON`, `TPR_CAL`, `TV_CAL`, `DVAG_CON`, `VVAG_CON`, `RSAG_CON` | 2–62 por etiqueta | 2,859–1,056,674 por etiqueta | Variable | Otras observaciones meteorológicas; semántica/unidad debe validarse etiqueta por etiqueta antes de uso |

El Manual de Control de Calidad IDEAM GDI-M005 v2 define precipitación `PTPM_CON` como acumulado del día pluviométrico 07:00 a 07:00, en milímetros, y describe `TSSM_CON` y sus derivados diarios; también identifica `TSSM_MX_D`, `TSSM_MN_D` y `TSSM_MEDIA_D`. Para media diaria indica la dependencia de las tres lecturas y sus reglas de cálculo. `BSHG_TT_D` se calcula a partir de horas de brillo solar bajo requisitos de observación. Ver [Manual GDI-M005 v2](https://ideam.gov.co/sites/default/files/mapa-de-procesos/gdi-m005_manual_control_de_calidad_verificacion_v2.pdf). El archivo extraído no demuestra por sí mismo si esos controles fueron aplicados al dato individual.

El nombre local termina en `PTPM_CON_INTER`; la relación exacta de este sufijo con el código documentado `PTPM_CON` no queda acreditada en el archivo ni se debe asumir como equivalencia definitiva sin metadato de descarga. La cobertura se reporta por la etiqueta original. El manual advierte revisar acumulados de precipitación diaria superiores a 135 mm; esa regla es alerta de revisión, no permiso para eliminar datos.

### 4.3 Cobertura anual 2012–2022

Se calculó `días con valor válido / días calendario del año` para cada estación-variable-año. La cobertura de `TSSM_CON` es cobertura de fechas con registro, no comprobación de que estén presentes las tres horas en cada fecha. En años bisiestos el denominador es 366. Para mostrar estaciones/años relativamente completos se usa ≥80% como umbral descriptivo.

| Variable | Estaciones Nariño | Estación-año con ≥80% de días | Estaciones con ≥80% en los 11 años | Estaciones con ≥80% en ≥9 años | Comentario |
|---|---:|---:|---:|---:|---|
| `PTPM_CON_INTER` | 99 | 607/1,089 | 41 | 53 | En cada año hay entre 50 y 57 estaciones que alcanzan el umbral |
| `TSSM_MN_D` | 22 | 156/242 | 9 | 13 | 13–15 estaciones/año alcanzan el umbral |
| `TSSM_MX_D` | 22 | 156/242 | 9 | 13 | 13–15 estaciones/año alcanzan el umbral |
| `TSSM_MEDIA_D` | 22 | 159/242 | 9 | 13 | 13–16 estaciones/año alcanzan el umbral |
| `HR_CAL_MEDIA_D` | 23 | 130/253 | 7 | 9 | Cobertura numérica calculada, pero semántica/unidad pendientes |
| `BSHG_TT_D` | 21 | 100/231 | 2 | 5 | Otras variables; interpretación diaria según manual requiere validar su cómputo |
| `EVTE_CON` | 22 | 131/242 | 2 | 9 | Otras variables; amplitud de cobertura variable |
| `NB_CON` | 22 | 183/242 | 10 | 15 | Otras variables; variable codificada/categórica por confirmar |
| `FA_CON` | 62 | 73/682 | 0 | 1 | Presencia irregular |
| `RCAM_CON` | 17 | 132/187 | 8 | 11 | Otras variables |
| `TPR_CAL` | 20 | 134/220 | 5 | 11 | Etiqueta no resuelta en el glosario revisado |
| `TV_CAL` | 22 | 156/242 | 8 | 13 | Etiqueta no resuelta en el glosario revisado |
| `DVAG_CON` / `VVAG_CON` | 8 cada una | 12/88 cada una | 1 | 1 | Datos subdiarios; el conteo diario no representa integridad intradía |
| `RSAG_CON` | 2 | 0/22 | 0 | 0 | Sin cobertura ≥80% diaria en 2012–2022 según los archivos leídos |

Las series de precipitación, mínima, máxima y media contienen fechas dentro de 2012–2022, pero ninguna estación puede declararse completa por su sola fecha inicial/final. Para esas variables hay estaciones con datos en los once años y con cobertura anual ≥80%; las demás tienen faltantes internos. Las tablas con cobertura por estación-año y el resumen por archivo permiten identificar exactamente días y años disponibles. Para humedad, no usar hasta confirmar etiqueta, unidad, frecuencia y fórmula con IDEAM.

### 4.4 Calidad, anomalías y límites

- En los 414 archivos Nariño (aprox. 6.3 millones de filas históricas sumadas entre variables), no se detectaron fechas vacías/inválidas, valores vacíos/no numéricos, filas idénticas, marcas de fecha-hora duplicadas ni registros fuera de orden. Esto verifica sintaxis y duplicación dentro de cada archivo; no prueba que no haya duplicación semántica entre catálogos o archivos de distinta versión.
- Se contaron 511 observaciones de precipitación mayores a 135 mm en el historial completo revisado; deben revisarse contra el manual y metadatos originales, no eliminarse automáticamente. El resumen adjunto ubica cada estación y el conteo, pero el conteo abarca fechas fuera del periodo objetivo también.
- Se encontraron negativos en etiquetas compatibles con evaporación (`EVTE_CON`: 47) y temperatura (`TPR_CAL`: 162; `TSSM_CON`: 2; `TSSM_MN_D`: 2; `TV_CAL`: 2); sin semántica/unidad completa, se clasifican como sospechosos a revisar, no errores confirmados. Los conteos son de todo el periodo histórico del archivo.
- Las precipitaciones en cero son frecuentes (604,758 en todo el historial) y no son automáticamente errores. La guía IDEAM requiere revisión de registros extremos y controles específicos, que no aparecen como columnas en los `.data`.
- Los archivos permiten revisar cobertura diaria para temperatura derivada y precipitación. No acreditan nivel de validación, unidades fuente, huso horario, cambios de instrumento, homogeneidad, ni tratamiento de cambios de estación. El límite físico y semántico es por estación, no cobertura de todos los municipios.
- `VVAG_CON` y `DVAG_CON` presentan muchos más registros que días: son subdiarios. No tratarlos como una cifra diaria sin definir agregación y verificar unidades/frecuencia.

## 5. Matriz de aptitud

| Fuente | Variable | Periodo requerido | Periodo disponible | Cobertura municipal/estaciones | Calidad | Estado | Acción requerida |
|---|---|---|---|---|---|---|---|
| DANE 2005–2017 | Población total 0–4 | 2012–2017 | 2005–2017 | 64 municipios Nariño cada año; sin vacíos | Claves únicas; 0 nulos usados; total = hombres + mujeres | APTA CON LIMITACIONES | Filtrar área `Total`, armonizar `MPIO` como código; preservar libro/versionado |
| DANE 2018–2042 | Población total 0–4 | 2018–2022 | 2018–2042 | 64 municipios Nariño cada año; sin vacíos | Claves únicas; 0 nulos usados; total = hombres + mujeres | APTA CON LIMITACIONES | Igual; tener en cuenta que `MPIO`/`DPMP` cambian de significado entre libros |
| IDEAM `PTPM_CON_INTER` | Precipitación diaria | 2012–2022 | Fechas históricas hasta 2026-08-12 | 99 estaciones en 44 etiquetas municipales; 41 estaciones con ≥80% en todos los 11 años | 511 >135 mm en toda la historia; sin flags/unidad en dato extraído | APTA CON LIMITACIONES | Confirmar sufijo/unidad y versión; revisar extremos; definir estación representativa y día pluviométrico 07–07 |
| IDEAM `TSSM_MN_D` | Temperatura mínima diaria | 2012–2022 | 1979–2026 en archivos | 22 estaciones en 16 etiquetas municipales; 9 con ≥80% todos los años | Sin flags/unidad en archivo; dos negativos a revisar | APTA CON LIMITACIONES | Confirmar metadatos y estado de calidad; definir selección de estación |
| IDEAM `TSSM_MX_D` | Temperatura máxima diaria | 2012–2022 | 1979–2026 en archivos | 22 estaciones en 16 etiquetas municipales; 9 con ≥80% todos los años | Sin flags/unidad en archivo | APTA CON LIMITACIONES | Confirmar metadatos y estado de calidad; definir selección de estación |
| IDEAM `TSSM_MEDIA_D` | Temperatura media diaria | 2012–2022 | 1976–2026 en archivos | 22 estaciones en 16 etiquetas municipales; 9 con ≥80% todos los años | Sin flags/unidad en archivo | APTA CON LIMITACIONES | Confirmar fórmula aplicada y metadatos; seleccionar estación |
| IDEAM `HR_CAL_MEDIA_D` | Posible humedad relativa media | 2012–2022 | 1976–2026 en archivos | 23 estaciones en 16 etiquetas municipales; 7 con ≥80% todos los años | Código/unidad no confirmados | PENDIENTE | Solicitar ficha de variable/unidad, aprobación y frecuencia a IDEAM |
| IDEAM resto de etiquetas | Otras variables meteorológicas | Según necesidad | Variable | Cobertura desigual, detallada en CSV | Varias etiquetas/unidades por resolver | PENDIENTE | Obtener glosario y metadatos específicos antes de seleccionar |
| SIVIGILA evento 995 | Casos IRA | 2012–2022 | No re-auditado en esta segunda auditoría | Fuera del alcance aquí | No se repitió validación epidemiológica | PENDIENTE para integración | Mantener la auditoría previa separada y revalidar al iniciar integración |

## 6. Limitaciones y próximos pasos

1. Solicitar o recuperar los ZIP oficiales originales y conservar fecha de descarga, tamaño y hash; documentar si la extracción local corresponde a esa versión.
2. Solicitar a IDEAM glosario/diccionario para `PTPM_CON_INTER`, `HR_CAL_MEDIA_D`, `TPR_CAL` y `TV_CAL`, unidades y reglas de control; pedir aclaración sobre banderas y datos preliminares/definitivos.
3. Fijar una edición oficial del catálogo de estaciones. Validar identificadores, coordenadas, altitud y cambios de estación/código; resolver diferencias entre el CSV de 9,914 códigos únicos y el CNE de 4,522 entradas sin empalmarlos por nombre aproximado.
4. Definir un criterio documentado para escoger estación(es) por municipio y agregación semanal. No asignar automáticamente la estación más cercana; si se consideran estaciones compartidas/interpolación, justificarlo y mantener datos faltantes explícitos.
5. Para temperatura observada a varias horas, verificar disponibilidad de las tres lecturas cuando se evalúen valores diarios; para precipitación, respetar el día pluviométrico 07:00–07:00 y documentar su alineación con semana epidemiológica.
6. Revisar extremos y negativos por estación/fecha con guías y metadatos IDEAM. No corregir ni eliminar automáticamente.
7. En una siguiente etapa, unir población DANE y variables meteorológicas a SIVIGILA solo después de aprobar reglas territoriales, temporales y de estación; conservar fuente, calidad y cobertura por cada valor.

**Dictamen:** la población municipal anual ya está respaldada para 2012–2022. Las variables diarias clave existen en los archivos locales y tienen subconjuntos de estaciones con cobertura repetida suficiente para evaluación. Sin embargo, la falta de procedencia verificable de los ZIP, banderas de calidad y reglas de asignación municipal impide considerar listo el dataset municipal-semanal integrado. Se puede avanzar a un piloto de selección y validación de estaciones; la integración definitiva aún no.

## 7. Archivos de evidencia

- [Resumen de auditoría IDEAM por estación-variable](resumen_ideam_narino_archivos.csv)
- [Cobertura IDEAM por estación-variable-año](cobertura_ideam_narino_estacion_anio.csv)

Los CSV son tablas de auditoría derivadas para evidenciar cobertura y controles; no son datasets analíticos integrados ni contienen imputaciones.
