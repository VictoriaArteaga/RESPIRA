# RESPIRA — Quinta auditoría: fuentes, integración y viabilidad del dataset definitivo

**Fecha:** 5 de noviembre de 2026
**Tipo:** análisis de solo lectura. No se modificó ningún dataset, no se imputó, interpoló, eliminó ni consolidó nada, no se tocó PostgreSQL/Supabase, no se ejecutaron migraciones, no se implementó IA, no se hicieron commits ni push. Los únicos archivos nuevos son los ocho de esta carpeta.

Archivos de esta auditoría: `INFORME_GENERAL.md` (este), `MATRIZ_COMPATIBILIDAD_FUENTES.csv`, `EVALUACION_DATASET_PILOTO.csv`, `EVALUACION_ESTACIONES_IDEAM.csv`, `EVALUACION_VARIABLES_SIVIGILA.csv`, `EVALUACION_POBLACION_DANE.md`, `VIABILIDAD_MODELOS.md`, `PROPUESTA_DATASET_DEFINITIVO.md`.

---

## 0. Resumen ejecutivo

1. **Los originales sí existen**, pero no en esta carpeta del proyecto: están en `..\RESPIRA - copia\data\` (SIVIGILA 2012–2022, DANE municipal 2005–2017 y 2018–2042, catálogo IDEAM y las series diarias `.data`). Los SHA-256 de los 6 archivos que ya tenían hash en `reports/cuarta_auditoria/sha256_fuentes.csv` coinciden con los de esa copia. Esto permitió **verificar de forma independiente** lo que las auditorías anteriores solo habían descrito.
2. **El piloto se reproduce exactamente.** Recalculado desde los originales: 312/312 valores de IRA, 312/312 conteos de filas, 312/312 valores y conteos de días de las tres temperaturas y 6/6 poblaciones coinciden con el CSV. El piloto es **correcto como cálculo, pero insuficiente como dataset**: 3 municipios × 2 años.
3. **La sospecha de truncamiento de SIVIGILA 2021 queda refutada en su forma original.** La hoja `ACUMULADO` declara 1.048.576 filas, pero solo **219.207 contienen datos**; las otras 829.367 son filas vacías. Los registros están distribuidos de forma uniforme por semana (3.875–4.363 filas/semana) y Nariño tiene 7.162 filas, en línea con 2020 (7.503) y 2022 (7.191). Falta aún un conteo oficial para afirmar completitud, pero **ya no hay evidencia de que el límite de Excel haya cortado el archivo**. Esto corrige lo dicho en `reports/auditoria_integridad_sivigila_2021.md`.
4. **Los «reportes repetidos» no son un caso aislado.** En Nariño hay 827 grupos (1.705 filas) con el mismo municipio-año-semana-UPGD-sede, **todos en 2012–2018** y ninguno en 2019–2022. `NUM_CON` se comporta como un contador secuencial de reportes por UPGD, no como identificador de paciente. Sumar o no sumar cambia el conteo anual hasta 4,5% (2012) y ≤0,6% desde 2015. No se consolidó nada; la regla sigue pendiente.
5. **Meteorología útil es escasa.** Solo **12 de 64 municipios** tienen una estación con temperatura mín/máx/media en ≥80% de las semanas 2012–2022 (≥6/7 días) y **38** tienen precipitación, esta última con etiqueta no confirmada. Una de las 12 estaciones (Aldana, 52055230) tiene `TSSM_MN_D` idéntica a `TSSM_MX_D` los 4.016 días: cobertura alta, calidad inutilizable.
6. **DANE es la fuente más sólida:** 704/704 municipio-año (64 municipios × 2012–2022), pero con un **salto de serie 2017→2018** (mediana +8,2%) por el cambio de libro y de base de proyección.
7. **El conteo de IRA tiene quiebres estructurales**, no solo estacionalidad: el total anual de Nariño pasa de 54.738 (2019) a 18.476 (2020) y 23.038 (2021) y vuelve a 48.415 (2022); además el volumen de consultas totales (`totcext_1..3`) cambia 42% entre 2013 y 2014. Un modelo entrenado sin tratar esto aprendería el cambio de notificación y no la enfermedad.
8. **Existen variables útiles que el piloto ignora:** `totcext_1..3` (consultas totales, un denominador natural), `ajuste`/`fec_aju`, y el contador `num_con`.
9. **La regla de calendario documentada («primer domingo en o después del 1 de enero») solo es válida para 2016 y 2022.** Se equivoca 7 días en 2013, 2014, 2018, 2019 y 2020 y no prevé las 53 semanas de 2014 y 2020, que sí aparecen en los datos de SIVIGILA.
10. **Ningún modelo es defendible aún como «de producción».** Hay un camino viable para un primer modelo **exploratorio** con 12 municipios (detalle en `VIABILIDAD_MODELOS.md`), condicionado a decisiones que pertenecen a ustedes (sección 9).

---

## 1. Alcance, método y disponibilidad de archivos

### 1.1 Método

- Lectura de los informes y CSV existentes del repositorio y verificación de sus afirmaciones contra los originales.
- Lectura **en streaming y solo lectura** de los 11 libros SIVIGILA (hoja de detalle de cada año), de los dos libros DANE municipales y de 165 series diarias IDEAM (99 estaciones candidatas). No hay librerías Excel instaladas, así que se usó un lector propio con la biblioteca estándar de Python. De SIVIGILA solo se extrajeron campos no personales y solo filas con `cod_mun` que empieza por 52. Los campos de contacto (`diligencia`, `cargo`, `telefono`, `correo`) y de identificación institucional no se copiaron a ningún archivo.
- Los scripts de análisis y los intermedios están en el directorio temporal de la sesión, no en el repositorio (la restricción era generar solo los informes). Si quieren conservarlos como código reproducible, puedo moverlos a `data/scripts/` en una tarea aparte.

### 1.2 Disponibilidad de los archivos pedidos

| Archivo solicitado | Estado | Ubicación / nota |
|---|---|---|
| `data/reports/resumen_ideam_historico.csv` | Disponible | 5 filas. **No es un resumen de series diarias**: resume los CSV DHIME de «temperatura máxima absoluta anual» (valores anuales, 2013–2026, 5 estaciones). No sirve para cobertura diaria. |
| `data/reports/resumen_ideam_narino_archivos.csv` | Disponible | 414 filas × 25 columnas (por archivo de estación-variable). |
| `data/reports/cobertura_ideam_narino_estacion_anio.csv` | Disponible | 4.554 filas × 13 (100 estaciones, 16 variables, 2012–2022). Las copias en `docs/data-audit/segunda-auditoria/` son idénticas. |
| `reports/estaciones_candidatas_ideam.csv` | Disponible | 99 estaciones × 38 columnas. |
| `reports/metadatos_variables_ideam.csv` | Disponible | 8 etiquetas. |
| `reports/diccionario_sivigila_995.csv` | Disponible | 14 filas. |
| `reports/cuarta_auditoria/filas_repeticion_sivigila.csv` | Disponible | 2 filas (Chachagüí 2016 SE43). |
| Libros SIVIGILA 2012–2022 | Disponibles **fuera del árbol** | `..\RESPIRA - copia\data\SIVIGILA\Datos_{año}_995.xlsx` (11 libros). |
| DANE municipal 2005–2017 y 2018–2042 | Disponibles fuera del árbol | Misma carpeta `data`. |
| `PPED-AreaSexoEdadNac-2018-2070.xlsx` | **No disponible** | No está en ninguna de las dos carpetas. La primera auditoría lo describe como nacional, sin municipios ni DIVIPOLA; los libros municipales lo sustituyen para este propósito. |
| `data/processed/pilot/version_pira_2016_2022.csv` | **No existe** | El archivo real se llama `piloto_respira_2016_2022.csv`. |
| `reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv` | Disponible | 312 × 29. |
| `backend/data/simulated/ira_cases.csv` | Disponible | 1.560 × 11, sintético (`data_source = DATOS SINTÉTICOS DE PRUEBA`). |
| `backend/respira.db`, `backend/tests/test.db` | No re-inspeccionados | Se confía en `reports/auditoria_integral_datasets_20261104.md` (sintéticos). |

Hashes SHA-256 de los originales usados: Anexo B.

---

## 2. Información meteorológica (IDEAM)

Detalle por estación: `EVALUACION_ESTACIONES_IDEAM.csv` (99 filas × 50 columnas).

### 2.1 Qué hay

- 99 estaciones candidatas en 44 municipios de Nariño (según nombre de municipio del catálogo). 63 activas, 34 suspendidas, 2 en mantenimiento.
- **Precipitación** `PTPM_CON_INTER`: archivo para las 99. **Temperatura** `TSSM_MN_D`, `TSSM_MX_D`, `TSSM_MEDIA_D`: archivo para solo 22 estaciones (77 estaciones no tienen temperatura).
- Los `.data` tienen solo `Fecha|Valor`, sin unidad, sin bandera de calidad, sin nivel de aprobación.

### 2.2 Cobertura por semana epidemiológica (≥6 de 7 días), 2012–2022

Se evaluaron las 574 semanas epidemiológicas del periodo (52 por año, 53 en 2014 y 2020). Esta métrica es más exigente que la cobertura diaria y es la que importa para una variable semanal.

| Variable | Estaciones con archivo | Con ≥80% de semanas | Con ≥95% de semanas | Con 7/7 días ≥80% de semanas |
|---|---:|---:|---:|---:|
| Precipitación | 99 | 53 (38 municipios) | 45 | 53 |
| Temp. media | 22 | 12 | 10 | — |
| Temp. mínima | 22 | 12 | 9 | — |
| Temp. máxima | 22 | 12 | 9 | — |

Estaciones de temperatura con series suficientemente completas (TSSM_MEDIA_D, % de semanas con ≥6/7 días):

| Estación | Municipio (catálogo) | Altitud | % semanas | Mayor racha sin semana válida | Observación |
|---|---|---:|---:|---:|---|
| 52055230 Aeropuerto San Luis | Aldana | 2.961 m | 100,0 | 0 | **MN = MX en 4.016/4.016 días y media > máx en 4.016/4.016: no usar mín/máx** |
| 52055210 Botana | Pasto | 2.820 m | 100,0 | 0 | |
| 52045020 Aeropuerto Antonio Nariño | Chachagüí | 1.796 m | 99,8 | 1 | Aeropuerto de Pasto, catalogado en Chachagüí |
| 52055060 Tanama | Samaniego | 1.500 m | 99,5 | 1 | |
| 52045030 San Bernardo | San Bernardo | 2.190 m | 99,1 | 5 | |
| 52055200 Funes | Funes | 2.181 m | 98,3 | 5 | |
| 52045040 Taminango | Taminango | 1.875 m | 97,6 | 5 | |
| 51025090 Granja El Mira | Tumaco | 16 m | 96,7 | 14 | Estado «En mantenimiento» |
| 52055220 El Paraíso | Túquerres | 3.033 m | 96,5 | 12 | |
| 52055090 Sindagua | Tangua | 2.800 m | 95,1 | 23 | |
| 52045090 El Común | Pupiales | 3.141 m | 93,9 | 5 | |
| 47015080 Monopamba | Puerres | 1.776 m | 80,7 | 39 | Solo 8 de 11 años con ≥80% |
| 47015100 El Encano | Pasto | 2.830 m | 76,8 | 8 | Bajo el umbral |
| 52055030 Bombona | Consacá | 1.493 m | 66,6 | 12 | En mantenimiento |
| 52045010 Obonuco | Pasto | 2.710 m | 64,3 | 102 | |
| 51035020 CCCP del Pacífico | Tumaco | 1 m | 35,4 | 257 | |

Las otras 6 estaciones con archivo de temperatura tienen cobertura entre 0% y 22%.

**No confundir estación con variable.** Hay estaciones activas con precipitación completa y sin ningún archivo de temperatura. Por ejemplo, de los 44 municipios con alguna estación, solo 16 tienen una estación con archivo de temperatura y solo 12 la tienen con cobertura ≥80%.

### 2.3 Municipios con cobertura útil

- **Temperatura (12):** Pasto, Aldana (solo media, ver anomalía), Chachagüí, Funes, Puerres, Pupiales, Samaniego, San Bernardo, Taminango, Tangua, Tumaco y Túquerres.
- **Precipitación (38):** ver Anexo C. Condicionada a confirmar con IDEAM el sufijo `_INTER`.
- **Sin ninguna estación candidata:** 20 de 64 municipios.

### 2.4 ¿Se puede asignar una estación a un municipio?

**Técnicamente justificable solo de forma limitada.** Lo que sí está demostrado: identidad de la estación por código exacto y su municipio en el catálogo. Lo que **no** está demostrado: que esa estación represente al municipio.

- Nariño tiene un gradiente altitudinal extremo (las estaciones con temperatura van de 1 m a 3.141 m). La temperatura baja del orden de 6 °C por cada 1.000 m; una estación en otra franja de altitud que la cabecera municipal no es una aproximación neutra.
- La asignación actual es **por nombre de municipio del catálogo**, no por distancia, altitud ni población. Chachagüí está representado por la estación del aeropuerto de Pasto; Pasto tiene cuatro estaciones con cobertura muy distinta.
- Faltan la altitud y las coordenadas de las cabeceras municipales para evaluar la diferencia con la estación. Esa evaluación no se hizo.

**Recomendación (a decidir por ustedes):** primera versión solo con municipios que tengan estación propia en el catálogo y cobertura suficiente, documentando la limitación de representatividad en cada fila; no asignar estaciones de municipios vecinos ni interpolar hasta aprobar un criterio de distancia/altitud. Alternativas en `PROPUESTA_DATASET_DEFINITIVO.md`.

### 2.5 Problemas de nombres, códigos, unidades y periodicidad

| Tema | Hallazgo |
|---|---|
| Catálogo nacional | 19.828 filas pero 9.914 códigos únicos: cada código está duplicado de forma idéntica. |
| Catálogo vs CNE vs `NARI_O.csv` | Tres listados de alcance distinto (9.914, 4.522 y 168 códigos); códigos de 8 dígitos rellenados a 10 con ceros en `NARI_O.csv`. No unir por nombre. |
| Nombre de municipio | Variantes: «Chachaguí» (catálogo) vs «Chachagüí» (DANE); nombres con paréntesis («Colón (Génova)», «Magüí (Payán)»). Tumaco, El Tablón y Santa Cruz no coinciden con DANE («San Andrés de Tumaco», «El Tablón de Gómez», «Santacruz») y requieren mapeo manual. |
| Codificación | Los CSV de cobertura/resumen están en UTF-8 con BOM y la columna `Año` es correcta byte a byte; la corrupción de «Año» que mencionó `auditoria_integral_datasets_20261104.md` aparece al abrirlos con otra codificación, no es un defecto del archivo. |
| Unidades | Ninguna en los `.data`. Temperatura en °C solo por el manual IDEAM GDI-M005; precipitación en mm solo por el manual y para `PTPM_CON`, no para `PTPM_CON_INTER`. |
| Periodicidad | Fecha con sello 07:00:00 en todas las series. En precipitación, el «día pluviométrico» es 07:00–07:00; no está documentado si el valor sellado el día D es el acumulado de D-1→D o de D→D+1 (afecta como mucho 1 día en el borde de cada semana). |
| Valores | `TSSM_MEDIA_D` tiene decimales largos (media de tres lecturas). 127 días con >135 mm de lluvia en 2012–2022 (alerta de revisión del manual, no se eliminan). 0 negativos en 2012–2022 en las series evaluadas. 0 fechas duplicadas y 0 valores no numéricos en las 165 series. |
| Coherencia física | Las 22 estaciones de temperatura cumplen mín ≤ máx. La única violación es la de Aldana (media > máx todos los días y MN = MX). |
| Resumen histórico | `resumen_ideam_historico.csv` y los CSV DHIME corresponden a valores anuales, no a diarios. |

### 2.6 De observaciones diarias a variables semanales sin inventar datos

Procedimiento propuesto (es el que ya usa el piloto, formalizado):

1. **Unidad temporal:** semana epidemiológica domingo–sábado con calendario anual validado (Anexo A), no ISO, no «7 días móviles».
2. **Agregación por variable:** mínima semanal = mínimo de `TSSM_MN_D`; máxima semanal = máximo de `TSSM_MX_D`; media semanal = promedio de `TSSM_MEDIA_D`. Para precipitación, suma semanal.
3. **Regla de suficiencia:** se emite valor semanal solo si hay ≥6 de 7 días válidos (temperatura). Para la **suma** de precipitación la regla debería ser 7/7 (una semana con 6 días sumados subestima el total sin avisar); la variante «6/7» solo es defendible para media, mínimo y máximo. Se necesita aprobación (decisión 3).
4. **Siempre se guardan** `n_dias_validos` y `cobertura_pct`; si no se cumple la regla el valor es NA con motivo. No se imputa, no se interpola, no se usa «el último valor conocido».
5. **No se usa** `TSSM_CON` (tres lecturas subdiarias) como si fuese un dato diario.

Comprobado: este procedimiento reproduce exactamente las 312 filas de temperatura del piloto.

---

## 3. Información epidemiológica (SIVIGILA, evento 995)

Detalle de campos: `EVALUACION_VARIABLES_SIVIGILA.csv`.

### 3.1 Diferencias entre archivos

| Año | Hoja de detalle | Columnas (encabezado) | Filas de datos | Filas Nariño | UPGD Nariño | Semana máx. | Filas de grupos repetidos |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2012 | `995 52` | 77 | 144.298 | 5.071 | 147 | 52 | 472 |
| 2013 | `Hoja1` | 84 | 187.954 | 7.029 | 156 | 52 | 597 |
| 2014 | `Hoja1` | 84 | 178.566 | 7.490 | 165 | **53** | 242 |
| 2015 | `Hoja1` | 84 | 184.985 | 7.556 | 153 | 52 | 91 |
| 2016 | `Hoja1` | 84 | 231.881 | 8.026 | 161 | 52 | 149 |
| 2017 | `EVENTO 995` | 84 | 237.781 (391 filas vacías internas) | 7.748 | 158 | 52 | 64 |
| 2018 | `Hoja1` | 84 | 240.894 | 7.863 | 153 | 52 | 90 |
| 2019 | `Final` | 85 | 245.199 | 7.886 | 157 | 52 | 0 |
| 2020 | `995_2020_Depurada` | 84 | 215.729 | 7.503 | 158 | **53** | 0 |
| 2021 | `ACUMULADO` (encabezado en fila 2) | 84 | **219.207** (dimensión declarada 1.048.576) | 7.162 | 154 | 52 (39 filas nacionales con 53) | 0 |
| 2022 | `995` | 83 | 235.738 | 7.191 | 144 | 52 | 0 |

Cambios de esquema relevantes:

- **2012** tiene 77 columnas: no existen los totales (`tot_*`), tiene `demanda` y `sivigi2010`, y la etiqueta de evento es «MORBILIDAD POR IRAG» (frente a «IRA» en 2016–2022).
- **2019** añade `cod_dep`. **2022** no tiene `version`.
- `fec_not` mezcla números seriales de Excel y texto `dd/mm/aaaa` (2021).
- `cod_pre`/`cod_sub` cambian de formato (con y sin cero inicial, número vs texto).
- Hay hojas alternativas no leídas: `Base Recibida` (2012) y `Hoja1` resumida (2019); las auditorías anteriores indican que no deben sumarse a la hoja de detalle.

### 3.2 Variables con significado operativo

Resumen (el detalle y la evidencia por variable están en el CSV):

- **Verificadas:** `cod_eve`, `semana`, `año`.
- **Utilizables con restricciones:** `cod_mun` (hay 10 filas con código incongruente), `iracext_1..3`, `fec_not`, `cod_pre`/`cod_sub`, `ndep_notif`, `nmun_notif`, `nom_eve`, `version`.
- **Pendientes:** `num_con`, `ajuste`, `fec_aju`, `totcext_*`, `tot_iraext`, `iracext_4..7`, hospitalización, UCI y mortalidad.
- **No utilizables:** `demanda`, `sivigi2010`, `cod_dep`, y los datos de contacto y de institución.

**Indicador epidemiológico candidato:** `iracext_1 + iracext_2 + iracext_3` (IRA, consulta externa/urgencias, 0–4 años), tal como lo definió la cuarta auditoría. Pendientes de elegir: ¿conteo, proporción sobre `totcext_1..3`, o tasa sobre población DANE?

**Cuidado con el significado del conteo.** Los documentos previos lo llaman «consultas», «atenciones» y «pacientes» según el archivo. El formulario es colectivo y cuenta lo notificado por las UPGD que reportan; no hay personas únicas ni residencia. Las tasas crudas implícitas del piloto (0,16–0,66 consultas por menor de 5 años al año) son muy bajas para IRA, lo que sugiere que el numerador mide la cobertura de reporte tanto como la enfermedad.

### 3.3 Registros repetidos por municipio, semana y prestador

**Qué se encontró (no se eliminó nada):**

| Año | Grupos repetidos | Filas en grupos | % de municipio-semanas afectadas | Grupos con mismos valores IRA | Grupos con filas totalmente idénticas | Conteo anual: suma / último reporte |
|---:|---:|---:|---:|---:|---:|---:|
| 2012 | 225 | 472 | 7,4% | 118 | 99 | 1,045 |
| 2013 | 287 | 597 | 8,1% | 76 | 48 | 1,029 |
| 2014 | 119 | 242 | 3,3% | 33 | 20 | 1,011 |
| 2015 | 45 | 91 | 1,2% | 22 | 18 | 1,005 |
| 2016 | 74 | 149 | 2,1% | 17 | 6 | 1,006 |
| 2017 | 32 | 64 | 1,0% | 18 | 3 | 1,001 |
| 2018 | 45 | 90 | 1,3% | 19 | 10 | 1,004 |
| 2019–2022 | 0 | 0 | 0% | — | — | 1,000 |
| **Total** | **827** | **1.705** | | **303 (37%)** | **204 (25%)** | |

(Si dos filas son idénticas en todos los campos de IRA y consultas, los datos no permiten distinguir reenvío de segundo reporte con casualmente los mismos valores. Los 303 grupos con mismo IRA incluyen los 204 con filas idénticas.)

**Qué representa cada patrón, según la evidencia:**

1. **`NUM_CON` es un contador de reportes por UPGD, pero no aclara qué es cada fila repetida.** Sube exactamente +1 entre semanas consecutivas en 86–89% de los pares en 2019–2022 y en 60–71% en 2012–2016, lo que lo muestra como secuencia de reportes y no como ID de paciente. Dentro de los grupos repetidos, en cambio, los `NUM_CON` son consecutivos solo en 312 de 827 grupos (38%): en el resto hay números intermedios, de modo que no se puede asegurar que sean reenvíos inmediatos ni que sean correcciones posteriores. Además, **16 grupos comparten el mismo `NUM_CON` en dos o más filas** (2 en 2015, 12 en 2016, 2 en 2018), es decir, el mismo número de reporte aparece dos veces; en solo 2 de esos 16 las cifras son idénticas.
2. **No es un patrón de «ajuste»:** solo 92 de los 827 grupos (11%) contienen una fila con `ajuste = 7`. El campo `ajuste` no explica la mayoría de las repeticiones.
3. **Hay al menos dos tipos de repetición mezclados:** (a) filas con todas las cifras iguales (204 grupos; 202 con `NUM_CON` distinto), donde sumar **duplicaría** el conteo si son reenvíos; (b) envíos con cifras distintas (el resto), donde puede tratarse de una corrección (el último reemplaza) o de un complemento (suma). Los datos locales no permiten distinguirlos.
4. **Sensibilidad (solo informativa):** la diferencia entre sumar todos los reportes y quedarse con el de mayor `NUM_CON` es de 4,5% del conteo anual de Nariño en 2012, 2,9% en 2013, 1,1% en 2014 y ≤0,6% desde 2015. Pero afecta hasta 8,1% de los municipio-semanas en 2012–2013, y en una semana concreta la diferencia puede ser grande.
5. **El caso de Chachagüí 2016 SE43** (filas Excel 204616 y 207474, `NUM_CON` 263 y 264, valores 8 y 1) es un ejemplo de tipo (b) y no un caso excepcional.

**Reglas de consolidación:**

| Regla | Estado |
|---|---|
| Conservar todas las filas en la capa normalizada | Justificada |
| No tratar `NUM_CON` como ID de paciente ni usarlo para deduplicar filas | Justificada |
| Marcar los grupos repetidos con un indicador y guardar n.º de reportes | Justificada |
| No convertir semanas sin fila en cero | Justificada |
| Sumar los reportes de un grupo | **Pendiente** (puede duplicar) |
| Quedarse con el último reporte (mayor `NUM_CON`) | **Pendiente** (requiere confirmar que es corrección) |
| Tratar vacíos en `iracext_*` como cero | **No justificada** (ver 3.5) |

Dado que desde 2019 no hay repeticiones, **la regla afecta sobre todo a 2012–2018**. Si el primer dataset se limitara a 2019–2022, el problema desaparece, pero ese periodo contiene el quiebre de 2020–2021.

### 3.4 Qué representa `NUM_CON` según la evidencia

Un consecutivo por UPGD y por reporte (contador que avanza de forma casi monótona semana a semana), tal como indica el anexo INS 2016. No identifica pacientes ni casos. Hay 1 valor nulo en 2012. Entre semanas consecutivas hay saltos mayores a +1 en 11–34% de los pares (más frecuentes en 2012–2015) y retrocesos o repeticiones en 2–4%; no se investigó la causa.

### 3.5 Integridad y completitud

- **2021:** ver el resumen ejecutivo. Distribución semanal 2021 (Nariño y nacional) normal; la semana 52 tiene 3.946 filas nacionales frente a 4.154 en la 51. Hay **39 filas nacionales con semana 53 en un año epidemiológico de 52 semanas** que deberían revisarse (0 en Nariño). No se verificó la integridad frente a un conteo oficial.
- **Vacíos en numeradores:** `iracext_1..3` tienen celdas vacías (no ceros) en filas de Nariño: 155 filas en 2013, 11 en 2014, 34 en 2016, 34 en 2017, 38 en 2018. Un `SUM` que ignore vacíos las vuelve cero silenciosamente. Ninguna cae en los tres municipios del piloto en 2016/2022.
- **Códigos:** 1 fila de 2012 con código 52000; 2 filas de 2012 con código 52838 (Túquerres) y departamento «BOYACÁ»; 7 filas de 2014 con código 52356 (Ipiales) y departamento «BOGOTÁ». No se filtró por nombre de departamento, por lo que pueden existir filas de Nariño con código erróneo no detectadas.
- **Semanas sin fila por municipio (2012–2022, de 574):** mediana 546 (95,1%); mínimo 394 (68,6%) en Francisco Pizarro, 441 en Magüí, 445 en La Tola; 34 municipios con ≥95%. Francisco Pizarro tiene **1 sola semana con fila en 2020** y Nariño (municipio) 7 en 2014: hay huecos largos en municipios pequeños. Las semanas sin fila no distinguen entre no notificación y cero.
- **Escala:** la mediana semanal por municipio (sin 2020–2021) es <3 en 14 municipios y <10 en 46 de 64. Pasto (mediana ≈340 por semana en 2019/2022) y Tumaco (≈108) dominan el total.
- **Cambios de notificación:** el total de consultas de 0–4 años (`totcext`) pasa de 346.292 (2013) a 492.530 (2014) y a 209.003 (2020); la razón IRA/consultas baja de 0,26 (2012) a 0,04 (2020) y sube a 0,18 (2022).

---

## 4. Información demográfica (DANE)

Resumen; análisis completo en `EVALUACION_POBLACION_DANE.md`.

- Información disponible: población proyectada por municipio, área (Cabecera, Centros poblados, Total), sexo y edad simple, 2005–2017 y 2018–2042, con DIVIPOLA de 5 dígitos. **Hay desagregación municipal y edad simple 0–4.**
- 704 de 704 municipio-año para 2012–2022. Total 0–4 = hombres + mujeres en el 100% de las filas, sin duplicados ni nulos en los campos usados.
- No hay datos semanales, ni por residencia/UPGD, ni por afiliación.
- El libro nacional `PPED-AreaSexoEdadNac-2018-2070.xlsx` no está disponible y no era necesario.
- Limitaciones para tasas: salto de serie 2017→2018, municipios muy pequeños (13 con <500 menores de 5 años en 2022), y numerador no comparable con el denominador.

---

## 5. Datasets derivados

| Dataset | Filas × columnas | Fuentes | Qué hace | Estado |
|---|---|---|---|---|
| `data/processed/pilot/piloto_respira_2016_2022.csv` (v1) | 312 × 28 | SIVIGILA 2016/2022, IDEAM `.data` (3 estaciones), DANE (2 libros) | Suma de IRACEXT_1..3 por municipio-semana; mín/máx/media semanal con ≥6/7 días; población 0–4 anual constante | **Reproducido 100%.** Nombres/etiquetas inconsistentes. |
| `reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv` | 312 × 29 | Ídem | Mismos valores. Renombra el indicador (`..._patient_count`), cambia «duplicado» por «repetición» (1 celda de `quality_notes`) y agrega 2 columnas de estado | Idéntico en valores a v1. El nombre «patient_count» no está respaldado. |
| `data/processed/pilot/version_pira_2016_2022.csv` | — | — | — | **No existe** |
| `backend/data/simulated/ira_cases.csv` | 1.560 × 11 | Generación sintética (10 municipios × 2023–2025 × 52 semanas) | Datos de demostración | Etiquetado como sintético. Correlación casos–temperatura −0,16, casos–precipitación −0,03: no hay señal climática real. **Excluir de cualquier análisis.** |
| `backend/respira.db`, `backend/tests/test.db` | 1.560 / 10 filas | Sintéticas | SQLite de demostración y pruebas | No re-inspeccionadas |
| Tablas de auditoría IDEAM (resumen, cobertura, candidatas, metadatos) | ver sección 1.2 | `.data` IDEAM | Evidencia secundaria | Útiles; cobertura diaria verificable, pero no semanal ni de calidad |

**Problemas metodológicos que deben resolverse antes de reutilizar el piloto** (detalle en `EVALUACION_DATASET_PILOTO.csv`):

1. 3 municipios y 2 años: sin validación temporal posible.
2. Solo temperatura; sin precipitación ni denominador de consultas.
3. Nombre y semántica del indicador inconsistentes entre v1, v2 y el diccionario.
4. Referencias a la fuente por nombre de archivo, sin hoja/fila/hash por registro.
5. Población anual constante y con salto de serie.
6. Regla de calendario no generalizable.
7. Semanas sin fila (4) y reporte repetido (1) siguen sin regla.
8. Representatividad de la estación asignada no evaluada.

---

## 6. Matriz de compatibilidad entre fuentes

Completa en `MATRIZ_COMPATIBILIDAD_FUENTES.csv`. Resumen:

| Relación | Clave | Cobertura | Viabilidad |
|---|---|---|---|
| SIVIGILA + IDEAM | DIVIPOLA ↔ tabla estación→municipio; semana epi ↔ fecha diaria | 2012–2022; 12 municipios (temperatura), 38 (precipitación) | **Viable con restricciones** |
| SIVIGILA + DANE | DIVIPOLA + año | 2012–2022; 64 municipios | **Viable con restricciones** |
| IDEAM + DANE | Ninguna directa | — | **No viable de forma independiente** |
| SIVIGILA + IDEAM + DANE | DIVIPOLA + semana epi | 12 municipios con temperatura; 6.282 municipio-semanas con IRA completa y temperatura | **Viable con restricciones, para un subconjunto** |

---

## 7. Evaluación del piloto 2016–2022

**Veredicto: el piloto valida la metodología, pero el dataset debe reconstruirse.**

- **Integridad de registros:** 312 claves únicas; sin duplicados.
- **Semanas:** correctas para 2016 y 2022 (0 días de diferencia en 104 semanas).
- **Municipios:** DIVIPOLA correctos; solo 3.
- **Consolidación SIVIGILA:** reproducible (312/312) pero no consolidada; 1 grupo repetido y 4 semanas sin fila sin regla.
- **Cobertura meteorológica:** 310/312 semanas con las tres temperaturas.
- **Temperatura:** reproducida 312/312; coherente (mín ≤ media ≤ máx). Calidad sin banderas IDEAM.
- **Población:** reproducida 6/6; denominador anual.
- **Consistencia v1–v2:** valores idénticos; v2 solo cambia nombres y estados.
- **Trazabilidad:** parcial (nombre de archivo, sin hoja/fila/hash).

Lo que sí se puede aprovechar: las reglas (calendario, ≥6/7 días, conservar filas, NA ≠ 0), la estructura de columnas de cobertura y trazabilidad, y el código de `data/scripts/auditar_cuarta_respira.py` como punto de partida. Lo que **no** se puede aprovechar tal cual: el archivo como base del dataset definitivo, por su alcance (3 × 2) y por las inconsistencias señaladas.

---

## 8. Informe de cierre

**1. Qué datasets tenemos realmente.**
Tres fuentes originales, todas en `RESPIRA - copia\data` (SIVIGILA 995 2012–2022: 11 libros; IDEAM: catálogo + series diarias `.data`; DANE municipal en 2 libros). Un dataset derivado real (el piloto, en dos versiones con los mismos valores), un conjunto de tablas de auditoría IDEAM/SIVIGILA y un dataset **sintético** (`ira_cases.csv` y 2 SQLite) que no debe mezclarse con los reales.

**2. Qué fuentes tienen información histórica aprovechable.**
- SIVIGILA 2012–2022: aprovechable, con las reglas de repetición, vacíos y quiebres 2020–2021 pendientes.
- DANE 2012–2022: aprovechable, con salto 2017→2018.
- IDEAM: aprovechable para 12 municipios (temperatura) y 38 (precipitación, condicionado).

**3. Municipios con información epidemiológica y meteorológica coincidente.**
Los 12 con temperatura útil: Pasto (52001), Aldana (52022; solo temperatura media), Chachagüí (52240), Funes (52287), Puerres (52573), Pupiales (52585), Samaniego (52678), San Bernardo (52685), Taminango (52786), Tangua (52788), Tumaco (52835) y Túquerres (52838), con entre 426 y 565 semanas coincidentes cada uno. Sin Aldana, 11 municipios y 5.724 municipio-semanas. Detalle en el Anexo C.

**4. Variables que se pueden usar con confianza.**
`cod_eve`, `semana`, `año`; `iracext_1..3` (como conteo notificado, con restricciones); `temp_min/max/mean` semanal en las estaciones de cobertura alta; población 0–4 anual (DANE).

**5. Variables que requieren validación.**
`num_con`, `ajuste`, `totcext_*`, `PTPM_CON_INTER` (precipitación), humedad, todas las de hospitalización/UCI/mortalidad, el significado de «consulta» vs «paciente», la representatividad de estaciones.

**6. Limitaciones definitivas y resolubles.**
- *Definitivas con los datos actuales:* sin banderas de calidad IDEAM; el conteo no es incidencia ni personas únicas; municipio de notificación ≠ residencia; solo 12 municipios con temperatura; población anual, no semanal.
- *Resolubles:* regla de repetición (consulta al INS), significado de `ajuste` y `totcext_*` (formulario/diccionario INS), etiqueta de precipitación (IDEAM), calendario INS por año, completitud 2021 (conteo oficial), banderas IDEAM, representatividad (altitud de cabeceras municipales), ajuste del salto DANE.

**7. ¿Se aprovecha el piloto o se reconstruye?** Reconstruir con las reglas del piloto; no extenderlo parcheando el CSV.

**8. Qué versión del dataset propongo.** Una versión escalonada (detalle en `PROPUESTA_DATASET_DEFINITIVO.md`): **V1 (núcleo epidemiológico)** 64 municipios × 2012–2022 con DANE; **V2 (con temperatura)** los 12 municipios; **V3 (con precipitación)** solo tras confirmación de IDEAM. Cada versión conserva los mismos identificadores y se construye sin sobrescribir la anterior.

**9. Decisiones que necesitan aprobación antes de transformar.** Sección siguiente.

---

## 9. Decisiones metodológicas que necesitan su aprobación

Ninguna se ha tomado por ustedes. Para cada una indico mi recomendación como punto de partida.

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| 1 | Qué es el indicador | a) conteo `iracext_1..3`; b) proporción sobre `totcext_1..3`; c) tasa sobre población DANE | Guardar a) y b); decidir c) después de la consulta al INS. |
| 2 | Regla para reportes repetidos (2012–2018) | a) sumar; b) último `NUM_CON`; c) conservar los dos y marcar; d) limitar a 2019–2022 | c) en la capa normalizada; decidir a)/b) tras respuesta del INS y probar sensibilidad. |
| 3 | Suficiencia semanal | ≥6/7 o 7/7; para precipitación suma, 7/7 | ≥6/7 en mín/máx/media; 7/7 en suma de lluvia. |
| 4 | Asignación estación→municipio | solo estación propia; vecina por altitud/distancia; interpolación | Solo estación propia en V2; evaluar vecina en una fase posterior. |
| 5 | Periodo de modelado | 2012–2022 completo; excluir 2020–2021; solo 2019–2022 | Construir 2012–2022 completo y marcar 2020–2021; decidir exclusión al modelar. |
| 6 | 2021 | usar con aviso; excluir hasta conteo oficial | Usar con aviso: el límite de Excel quedó descartado, la completitud no. |
| 7 | Salto DANE 2017→2018 | dejarlo y marcarlo; reescalar; usar la serie 2018+ y retropolada | Dejarlo y marcarlo con un indicador de libro. Cualquier ajuste requiere criterio DANE. |
| 8 | Calendario | regla del 4 de enero verificada por año vs calendario INS descargado | Cargar el calendario INS de cada año como tabla versionada. |
| 9 | Aldana | excluir temperatura mín/máx; excluir estación | Excluir `TSSM_MN_D`/`TSSM_MX_D` de 52055230 hasta aclaración IDEAM. |
| 10 | Nombre del indicador | `consultas`, `atenciones`, `pacientes` | Neutro: `ira_ce_urg_0_4_notificado` hasta confirmar. |
| 11 | Consultas al INS/IDEAM/DANE | Enviar o no | Enviarlas; son las que más reducen incertidumbre. |
| 12 | Conservar scripts de análisis | En `data/scripts/` o descartar | Conservarlos. |

---

## Anexo A. Calendario epidemiológico 2012–2023

Regla verificada con los datos: SE1 es la semana domingo–sábado que contiene el 4 de enero (equivalente a «termina el primer sábado con ≥4 días en enero»). Confirmación independiente: las únicas semanas 53 en los libros SIVIGILA son las de 2014 y 2020, que es lo que predice esta regla. **Falta contrastarla con el calendario oficial INS de cada año** (decisión 8).

| Año | SE1 empieza (regla del 4 de enero) | Regla «primer domingo en o después del 1 de enero» | Diferencia | Semanas del año |
|---:|---|---|---:|---:|
| 2012 | 2012-01-01 | 2012-01-01 | 0 | 52 |
| 2013 | 2012-12-30 | 2013-01-06 | 7 d | 52 |
| 2014 | 2013-12-29 | 2014-01-05 | 7 d | **53** |
| 2015 | 2015-01-04 | 2015-01-04 | 0 | 52 |
| 2016 | 2016-01-03 | 2016-01-03 | 0 | 52 |
| 2017 | 2017-01-01 | 2017-01-01 | 0 | 52 |
| 2018 | 2017-12-31 | 2018-01-07 | 7 d | 52 |
| 2019 | 2018-12-30 | 2019-01-06 | 7 d | 52 |
| 2020 | 2019-12-29 | 2020-01-05 | 7 d | **53** |
| 2021 | 2021-01-03 | 2021-01-03 | 0 | 52 |
| 2022 | 2022-01-02 | 2022-01-02 | 0 | 52 |
| 2023 | 2023-01-01 | 2023-01-01 | 0 | 52 |

## Anexo B. Hashes SHA-256 de los originales usados (`RESPIRA - copia\data`)

Los marcados con ✔ coinciden con `reports/cuarta_auditoria/sha256_fuentes.csv`. Los demás son una línea base nueva (cierra parcialmente D-08/D-13 para estos archivos; no prueban identidad con la descarga oficial).

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| SIVIGILA/Datos_2012_995.xlsx | 92.264.928 | cc9a4311810a005f8c08d38432b089086b8c7b6a5936753d9210c55d62ec680d |
| SIVIGILA/Datos_2013_995.xlsx | 73.873.471 | 4952a2ee09bbf90c5fe06b027de6d65e0ca1cb470d6dc006f328a9988d8574fa |
| SIVIGILA/Datos_2014_995.xlsx | 63.497.745 | b7e99ab19c40e7c89616de1fd8b3ce52ec09b8d801a97d463cf3077c42e7665c |
| SIVIGILA/Datos_2015_995.xlsx | 65.648.298 | 0ebbfc83c760614e38c6301b06f42ecebea3e55b5952ff81cb3df95c5d7e46e4 |
| SIVIGILA/Datos_2016_995.xlsx ✔ | 81.232.572 | a68032ebb6f375ffdd28897abe6a5d33ac3cf50acb595bbbbf7733915084c92a |
| SIVIGILA/Datos_2017_995.xlsx | 84.909.437 | 4906e0b93d3f37a28a0acc16046adb34d2d26449dea9a1f3d8fe0e6ad2867950 |
| SIVIGILA/Datos_2018_995.xlsx | 88.692.007 | aa837613e3368e25dc6a42aa9bc8e9728c540cbd6d70bdee6e63b54bdc9909f0 |
| SIVIGILA/Datos_2019_995.xlsx | 119.179.432 | 1837bb2d649353489c198902062a86ed682c0602751eb48c3c027a6f891eba80 |
| SIVIGILA/Datos_2020_995.xlsx | 77.100.018 | f0456ba1c5088f95fdcbb494ac0d770c245b591df8c8d3b369c4b7fef397bb1c |
| SIVIGILA/Datos_2021_995.xlsx ✔ | 77.043.344 | 46eb6f0e4a16d9ef26dbf446a8f94b151ea96d1d8a28a0ad97e9a0da132677b5 |
| SIVIGILA/Datos_2022_995.xlsx ✔ | 85.118.826 | a3b5b74b1166c5dc461979d54d12ba910d3bd64f648ec82dc46ea931c2488310 |
| DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx ✔ | 55.969.926 | f804eb4408d2714c722b4031f6bc5af55efab55c6b32bdce4607e6dacb9dcb41 |
| PPED-AreaSexoEdadMun-2018-2042_VP.xlsx ✔ | 131.609.579 | 7e461635315664d44ba52cc7f951947085a0ea6f2dda72fe2efed11a76880516 |
| Cat_logo_Nacional_de_Estaciones_del_IDEAM (1).csv ✔ | 6.154.334 | 636fd5c7cd2fc3efcadb0f914f769d903247a2e3a9da00471cc0d698b229d4a5 |

Los `.data` IDEAM no se hashearon individualmente (165 archivos leídos). El hash de los tres usados por el piloto está en `sha256_fuentes.csv`.

## Anexo C. Cobertura por municipio (64 municipios)

«Semanas con fila SIVIGILA» cuenta semanas con al menos una fila, no semanas completas ni correctamente notificadas. «Mun-semanas IRA+temperatura» = semanas con IRA completa (sin vacíos en `iracext_1..3`) y las tres temperaturas con ≥6/7 días en la mejor estación del municipio, solo si esa estación cubre ≥80% de las semanas. Las estaciones asignadas por nombre de municipio no son una afirmación de representatividad. Para Aldana, `TSSM_MN_D` y `TSSM_MX_D` no son utilizables (ver 2.2).


| DIVIPOLA | Municipio | Semanas con fila SIVIGILA (de 574) | Pob. 0–4 2016 | Pob. 0–4 2022 | Mejor estación temperatura (% sem. ≥6/7) | Mejor estación precipitación (% sem. ≥6/7) | Mun-semanas IRA+temperatura |
|---|---|---:|---:|---:|---|---|---:|
| 52001 | Pasto | 572 | 25,747 | 23,755 | 52055210 (100.0%) | 52055210 (100.0%) | 565 |
| 52019 | Albán | 552 | 586 | 584 | — | — |  |
| 52022 | Aldana | 558 | 498 | 523 | 52055230 (100.0%) | 52055230 (99.7%) | 558 |
| 52036 | Ancuya | 530 | 447 | 446 | — | — |  |
| 52051 | Arboleda | 537 | 582 | 601 | — | 52040160 (97.6%) |  |
| 52079 | Barbacoas | 539 | 6,994 | 7,146 | 51025080 (20.4%) <80% | 51020010 (98.4%) |  |
| 52083 | Belén | 533 | 384 | 389 | — | — |  |
| 52110 | Buesaco | 549 | 1,504 | 1,561 | — | 52040060 (96.9%) |  |
| 52203 | Colón | 557 | 500 | 490 | — | 52030060 (98.3%) |  |
| 52207 | Consacá | 546 | 680 | 734 | 52055030 (66.5%) <80% | 52055030 (99.0%) |  |
| 52210 | Contadero | 534 | 519 | 534 | — | — |  |
| 52215 | Córdoba | 550 | 1,213 | 1,284 | — | — |  |
| 52224 | Cuaspud Carlosama | 559 | 715 | 759 | — | — |  |
| 52227 | Cumbal | 553 | 2,995 | 3,282 | — | 52050110 (100.0%) |  |
| 52233 | Cumbitara | 528 | 375 | 379 | — | 52080010 (100.0%) |  |
| 52240 | Chachagüí | 544 | 1,023 | 1,089 | 52045020 (99.8%) | 52045020 (100.0%) | 535 |
| 52250 | El Charco | 523 | 3,000 | 2,640 | — | 53020010 (92.7%) |  |
| 52254 | El Peñol | 544 | 347 | 352 | — | 52050010 (100.0%) |  |
| 52256 | El Rosario | 526 | 689 | 719 | — | 52010030 (99.1%) |  |
| 52258 | El Tablón de Gómez | 553 | 822 | 832 | — | 52040050 (99.1%) |  |
| 52260 | El Tambo | 541 | 833 | 809 | — | 52050170 (0.0%) <80% |  |
| 52287 | Funes | 546 | 373 | 389 | 52055200 (98.3%) | 52055200 (98.8%) | 537 |
| 52317 | Guachucal | 563 | 1,261 | 1,324 | — | — |  |
| 52320 | Guaitarilla | 548 | 629 | 626 | — | — |  |
| 52323 | Gualmatán | 550 | 363 | 389 | — | 52050100 (99.1%) |  |
| 52352 | Iles | 546 | 557 | 559 | — | — |  |
| 52354 | Imués | 547 | 379 | 383 | — | 52050090 (99.1%) |  |
| 52356 | Ipiales | 566 | 8,679 | 9,215 | — | 51020030 (0.0%) <80% |  |
| 52378 | La Cruz | 559 | 1,126 | 1,147 | — | 52030090 (97.2%) |  |
| 52381 | La Florida | 551 | 576 | 572 | — | — |  |
| 52385 | La Llanada | 553 | 584 | 581 | — | 52060040 (94.6%) |  |
| 52390 | La Tola | 445 | 915 | 816 | — | — |  |
| 52399 | La Unión | 568 | 2,022 | 2,172 | — | 52030030 (99.1%) |  |
| 52405 | Leiva | 534 | 638 | 653 | — | 52010060 (91.8%) |  |
| 52411 | Linares | 520 | 516 | 502 | — | 52050140 (99.1%) |  |
| 52418 | Los Andes | 544 | 697 | 684 | — | 52060020 (0.0%) <80% |  |
| 52427 | Magüí | 441 | 3,366 | 3,985 | — | 53020020 (100.0%) |  |
| 52435 | Mallama | 546 | 653 | 629 | — | — |  |
| 52473 | Mosquera | 526 | 997 | 1,042 | — | 53010020 (94.2%) |  |
| 52480 | Nariño | 489 | 284 | 298 | — | 52040070 (90.9%) |  |
| 52490 | Olaya Herrera | 557 | 3,204 | 3,356 | — | — |  |
| 52506 | Ospina | 553 | 440 | 438 | — | — |  |
| 52520 | Francisco Pizarro | 394 | 1,474 | 1,666 | — | 52090010 (94.8%) |  |
| 52540 | Policarpa | 532 | 601 | 604 | — | 52070030 (99.7%) |  |
| 52560 | Potosí | 549 | 887 | 758 | — | 52050190 (100.0%) |  |
| 52565 | Providencia | 527 | 440 | 413 | — | — |  |
| 52573 | Puerres | 540 | 616 | 612 | 47015080 (80.7%) | 52050120 (100.0%) | 426 |
| 52585 | Pupiales | 542 | 1,141 | 1,130 | 52045090 (93.9%) | 52045090 (97.7%) | 510 |
| 52612 | Ricaurte | 542 | 2,192 | 2,477 | 51025020 (0.0%) <80% | 51025020 (0.0%) <80% |  |
| 52621 | Roberto Payán | 523 | 1,536 | 1,570 | — | 52090020 (58.7%) <80% |  |
| 52678 | Samaniego | 558 | 1,805 | 1,717 | 52055060 (99.5%) | 52050020 (100.0%) | 550 |
| 52683 | Sandoná | 555 | 1,123 | 1,090 | — | 52050040 (95.1%) |  |
| 52685 | San Bernardo | 553 | 650 | 643 | 52045030 (99.1%) | 52045030 (100.0%) | 548 |
| 52687 | San Lorenzo | 538 | 1,132 | 1,098 | — | — |  |
| 52693 | San Pablo | 549 | 915 | 904 | — | — |  |
| 52694 | San Pedro de Cartago | 556 | 444 | 445 | — | — |  |
| 52696 | Santa Bárbara | 514 | 1,618 | 1,768 | — | — |  |
| 52699 | Santacruz | 547 | 791 | 781 | — | 52050050 (98.3%) |  |
| 52720 | Sapuyes | 557 | 418 | 419 | 52055100 (0.0%) <80% | 52055100 (0.0%) <80% |  |
| 52786 | Taminango | 524 | 893 | 907 | 52045040 (97.6%) | 52035040 (100.0%) | 510 |
| 52788 | Tangua | 544 | 840 | 872 | 52055090 (95.1%) | 52050080 (98.8%) | 499 |
| 52835 | San Andrés de Tumaco | 559 | 24,765 | 27,891 | 51025090 (96.7%) | 51025090 (100.0%) | 516 |
| 52838 | Túquerres | 556 | 2,828 | 2,785 | 52055220 (96.5%) | 52055220 (98.4%) | 528 |
| 52885 | Yacuanquer | 540 | 681 | 661 | — | — |  |
