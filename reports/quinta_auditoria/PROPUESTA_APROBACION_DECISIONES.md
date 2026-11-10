# Propuesta de aprobación de las 12 decisiones — Quinta auditoría RESPIRA

**Fecha:** 5 de noviembre de 2026. **Base:** `INFORME_GENERAL.md` (sección 9) y los demás entregables de `reports/quinta_auditoria/`. No se recalculó nada ni se ejecutó ninguna auditoría nueva; todas las cifras provienen de la quinta auditoría.

## 0. Estado formalizado de las decisiones (actualización del 5 de noviembre de 2026)

**Qué cambió.** La autora revisó esta propuesta y respondió: **A — SÍ** (aprobar las reglas V1, V2 y V3 con las condiciones y limitaciones documentadas), **B — SÍ** (conservar las dos variantes de reportes repetidos sin elegir una), **C — SÍ** (copiar los scripts pertinentes a `data/scripts/`) y **D — REVISIÓN** (preparar las consultas institucionales sin enviarlas). Las secciones 1 a 6 de más abajo conservan el análisis original sin cambios; esta sección 0 es la que rige el estado real. Ninguna aprobación condicionada se convirtió en definitiva.

### 0.1 Estado de las 12 decisiones

| # | Decisión | Estado formal | Base de la autorización | Condiciones que se mantienen |
|--:|---|---|---|---|
| 1 | Indicador de IRA | **Aprobada con condiciones** | A | Nombre fijo `iracext_0_4_notificado` (conteo notificado). La proporción sobre `totcext_1..3` se guarda aparte, marcada **pendiente de validar**. No se calculan tasas ni incidencias oficiales sin validación del denominador por el INS. |
| 2 | Reportes repetidos | **Aprobada parcialmente; interpretación PENDIENTE (INS)** | B | Se conservan todas las filas y las dos variantes `SUMA` y `ULTIMO_REPORTE` como interpretaciones alternativas; **ninguna es la oficial**. **Las dos variantes no se usan a la vez como predictores independientes** (son la misma información en dos versiones). `NUM_CON` no es identificador de pacientes. |
| 3 | Suficiencia semanal | **Aprobada** | A | ≥6/7 días en mínima, máxima y media; 7/7 en suma de lluvia. Se guardan `n_dias`; sin imputación ni interpolación. La lluvia sigue bloqueada hasta que IDEAM confirme `PTPM_CON_INTER`. |
| 4 | Asignación estación→municipio | **Aprobada con condiciones; Chachagüí PENDIENTE** | A | Solo estación propia del municipio y con cobertura ≥80% de semanas; sin vecinas ni interpolación. La estación de Chachagüí queda pendiente (ver 0.3). Representatividad (D-03) sigue siendo una limitación declarada. |
| 5 | Periodo de modelado | **Aprobada con condiciones** | A | 2012–2022 completo con marca de `regimen` (≤2019 / 2020–2021 / 2022). La exclusión de 2020–2021 se decide en cada experimento. |
| 6 | Año 2021 | **Aprobada con condiciones** | A | Incluido con la marca `completitud_no_verificada`. Pendiente el conteo oficial del INS. |
| 7 | Salto DANE 2017→2018 | **Aprobada con condiciones** | A | Se conserva y se marca con `dane_libro`. **No se reescala** la población. Pendiente el empalme oficial de DANE. |
| 8 | Calendario | **Aprobada con condiciones** | A | Tabla de calendario versionada por año. Los años no confirmados por el INS se identifican como tales (`calendar_verificado = NO`); solo 2016 y 2022 tienen verificación documentada. |
| 9 | Estación de Aldana (52055230) | **Aprobada** | A (instrucción explícita) | Se excluyen de temperatura **las tres variables** (`TSSM_MN_D`, `TSSM_MX_D` y `TSSM_MEDIA_D`). Se reincorpora solo si IDEAM aclara la anomalía. |
| 10 | Nombre del indicador | **Aprobada** | A | `iracext_0_4_notificado`. |
| 11 | Consultas institucionales | **Preparadas; envío NO autorizado** | D | Documentos `CONSULTA_INS.md`, `CONSULTA_IDEAM.md`, `CONSULTA_DANE.md` listos para revisión. No se envió nada. |
| 12 | Conservar scripts | **Aprobada y ejecutada** | C | 22 scripts copiados sin modificar, con hash verificado, en `data/scripts/quinta_auditoria/`; ver `INVENTARIO_SCRIPTS.md`. No se ejecutaron. |

### 0.2 Reglas transversales confirmadas

- La **ausencia de registros no es un cero**: una semana sin fila es `AUSENTE`.
- Los valores faltantes se conservan como `NULL` donde corresponda; **no hay imputación**.
- No se calculan tasas ni incidencias oficiales; el conteo es una notificación, no incidencia.
- Régimen 2020–2021 y `completitud_no_verificada` (2021) se mantienen en todas las versiones.
- Población DANE sin reescalar entre 2017 y 2018.
- Los calendarios no confirmados se rotulan como tales.
- Los datos sintéticos no se mezclan con los reales.
- Se mantienen las restricciones de cobertura (≥80% de semanas con ≥6/7 días para temperatura) y de calidad (sin banderas IDEAM; precipitación sin etiqueta confirmada).

### 0.3 Efecto sobre V2 de las decisiones 4 y 9

| Concepto | Cifra anterior | Cifra actual | Cómo se obtiene (documentado en `INFORME_GENERAL.md`) |
|---|---|---|---|
| Municipios con temperatura | 12 | **11** con Aldana excluida; de ellos **1 pendiente (Chachagüí)** y 10 sin objeción | Se excluye la estación 52055230 (decisión 9) |
| Municipio-semanas con IRA completa y temperatura | 6.282 | **5.724** sin Aldana; **5.189** si además se retira Chachagüí (5.724 − 535) | Anexo C: 535 municipio-semanas de Chachagüí |

Para V3 no cambia nada por la decisión 9 (la anomalía afecta solo a temperatura).

### 0.4 Hallazgo: estación asignada a Chachagüí

**Pregunta.** La regla aprobada es «solo estación del mismo municipio». ¿Contradice eso que la estación de Chachagüí sea el «aeropuerto de Pasto»?

**Hechos (verificados en los archivos):**

| Dato | Valor | Fuente |
|---|---|---|
| Código | 52045020 | Catálogo nacional IDEAM; `reports/estaciones_candidatas_ideam.csv` |
| Nombre en el catálogo | «AEROPUERTO ANTONIO NARIÑO [52045020]» | Ídem |
| Municipio en el catálogo | «Chachaguí» (sin diéresis), departamento Nariño | Catálogo (2 filas idénticas) y `NARI_O.csv` |
| Categoría / estado | Sinóptica Principal, convencional, activa | Ídem |
| Coordenadas | latitud 1,394083333; longitud −77,29086111; altitud 1.796 m | Ídem |
| Instalación | 15/11/1957 | Ídem |
| Criterio con el que se asignó a Chachagüí | Coincidencia exacta de **código de estación** y del campo **Municipio del catálogo**; no proximidad ni altitud | `reports/validacion_fuentes_y_piloto.md`, `reports/cuarta_auditoria_respira.md` |
| Otra estación catalogada en Chachagüí | 52040030 «CHACHAGUI», pluviométrica, suspendida, a 3,2 km; el catálogo le da altitud 20 m | `estaciones_candidatas_ideam.csv` |
| Estaciones catalogadas en Pasto más cercanas | Chimayoy (52055110), a 14,6 km; Col. Maridíaz (52040150 / 52045050), a 16,0 km | Distancias calculadas sobre las coordenadas del catálogo |

**Hallazgos:**

1. **Cumplimiento por catálogo: sí.** El catálogo IDEAM registra la estación en el municipio de Chachagüí. Con la definición operativa usada hasta ahora (municipio del catálogo), cumple la regla.
2. **Corrección de una afirmación mía.** En la quinta auditoría escribí que esta estación es «el aeropuerto de Pasto». **Esa afirmación no está respaldada por ningún archivo del repositorio**: el catálogo solo dice «Aeropuerto Antonio Nariño» y municipio Chachagüí. Procedía de mi conocimiento general y no la pude comprobar. Queda retirada como hecho. Las coordenadas son coherentes con la ubicación en Chachagüí (a 3,2 km de la otra estación de ese municipio y a ≥14 km de cualquier estación catalogada en Pasto), pero eso es una inferencia, no una demostración.
3. **No se puede demostrar la ubicación física dentro del polígono municipal.** No hay límites municipales (ni DIVIPOLA con geometría) en el repositorio ni en los datos auditados. La verificación solo puede basarse en el campo del catálogo.
4. **Limitación que no es exclusiva de Chachagüí:** la asignación de las demás estaciones (Funes, Samaniego, Pasto, etc.) también se apoya únicamente en el campo Municipio del catálogo y tampoco se verificó geográficamente.
5. **Representatividad:** que la estación esté en el municipio no prueba que represente su temperatura (D-03). Sigue pendiente para todas.
6. Hay una inconsistencia menor en el catálogo, ajena a la regla: la estación 52040030 tiene altitud 20 m, incompatible con su posición (≈3 km de una estación a 1.796 m). No se usa, pero indica que el campo altitud del catálogo puede tener errores.

**Conclusión.** No se demostró una contradicción con la regla tal como está formulada (catálogo), pero **tampoco se puede demostrar la ubicación física**. Siguiendo la instrucción, **Chachagüí queda PENDIENTE** de verificación geográfica. **No se cambió ninguna asignación**: el piloto, los CSV de la quinta auditoría y los cálculos permanecen como estaban, y los demás entregables de la quinta auditoría **todavía contienen la afirmación retirada** («aeropuerto de Pasto») en `INFORME_GENERAL.md` (tabla de 2.2 y sección 2.4), `EVALUACION_DATASET_PILOTO.csv` y `EVALUACION_ESTACIONES_IDEAM.csv`. No se editaron en esta ejecución; esta sección prevalece sobre ellos.

**Para cerrarlo hace falta (sin decidir nada aún):** los límites municipales de Nariño (IGAC/DANE) o la confirmación de IDEAM del municipio de ubicación de la estación (incluida en `CONSULTA_IDEAM.md`).

---

**Convención (del análisis original).** *Hecho* = comprobado en los originales o en documentos citados. *Inferencia* = deducción razonable no confirmada. *Recomendación* = propuesta de decisión. **Esta propuesta no aprueba nada por sí sola; la aprobación es de ustedes.**

**Estados:** **APROBABLE** (evidencia suficiente) · **CONDICIONAL** (aprobable con restricciones) · **PENDIENTE** (requiere INS, IDEAM o DANE, o una autorización suya).

---

## 1. Tabla resumen

| # | Decisión | Estado | Recomendación |
|--:|---|---|---|
| 1 | Indicador de IRA | CONDICIONAL | Guardar el conteo `iracext_1..3` y, aparte, la proporción sobre `totcext_1..3`; no calcular tasa ni llamarla incidencia hasta aclarar el INS |
| 2 | Reportes repetidos (2012–2018) | PENDIENTE (INS) | Conservar todas las filas y ambas variantes (suma y último `NUM_CON`) como columnas separadas; no elegir una |
| 3 | Suficiencia semanal | APROBABLE | ≥6/7 días para mínima, máxima y media; 7/7 para suma de lluvia |
| 4 | Asignación estación→municipio | CONDICIONAL | Solo estación propia del municipio y con cobertura suficiente; sin vecinas ni interpolación |
| 5 | Periodo de modelado | CONDICIONAL | Construir 2012–2022 completo y marcar 2020–2021; decidir exclusión al modelar |
| 6 | Año 2021 | CONDICIONAL | Incluir con aviso; el límite de Excel quedó descartado, la completitud no |
| 7 | Salto DANE 2017→2018 | CONDICIONAL | Conservarlo y marcarlo con `dane_libro`; sin reescalar |
| 8 | Calendario | CONDICIONAL | Tabla de calendario versionada por año; regla del 4 de enero solo como borrador hasta contrastar con el INS |
| 9 | Estación de Aldana | APROBABLE | Excluir `TSSM_MN_D` y `TSSM_MX_D` de 52055230 |
| 10 | Nombre del indicador | APROBABLE | Nombre neutro basado en el campo fuente: `iracext_0_4_notificado` |
| 11 | Consultas institucionales | APROBABLE (acción suya) | Enviar las preguntas de la sección 6 |
| 12 | Conservar scripts de análisis | PENDIENTE (su autorización) | Recomendado conservarlos, pero **no se ha hecho nada**: requiere su orden explícita |

---

## 2. Análisis por decisión

### Decisión 1 — Indicador de IRA
- **Qué se decide:** qué se predice o describe: conteo, proporción sobre consultas totales o tasa por población.
- **Evidencia (hechos):** el numerador es `iracext_1+2+3`, conteo colectivo notificado por las UPGD que reportan, por municipio notificador (no residencia). Los textos previos lo llaman "consultas", "atenciones" y "pacientes". Las tasas implícitas del piloto (0,16–0,66 por menor de 5 años y año) son bajas. `totcext_1..3` existe en los 11 libros, pero su significado se infirió por el nombre del campo. La razón IRA/consultas varía de 0,26 (2012) a 0,04 (2020) y 0,18 (2022). La mediana semanal es <10 en 46 de 64 municipios.
- **Opciones:** (a) conteo; (b) proporción; (c) tasa.
- **Evaluación:** (a) es lo que hay, pero mezcla enfermedad y volumen de reporte. (b) controla el volumen, pero el denominador no está validado. (c) depende de un denominador (DANE) que no corresponde al numerador y se inestabiliza en municipios pequeños (13 con <500 niños en 2022).
- **Recomendación:** guardar (a) y (b) como columnas distintas, la (b) marcada como "pendiente de validar". Posponer (c). En ningún documento ni columna llamar "incidencia" a estos valores.
- **Consecuencias:** V1: ambas columnas, sin tasa. V2/V3: igual; el objetivo se fija en el nivel de entrenamiento, no en el analítico.

### Decisión 2 — Reportes repetidos y uso de `NUM_CON`
- **Qué se decide:** cómo contar semanas con más de un reporte de la misma UPGD y sede.
- **Evidencia (hechos):** 827 grupos (1.705 filas) en Nariño, todos en 2012–2018; ninguno en 2019–2022. Afectan 7,4% y 8,1% de los municipio-semanas en 2012 y 2013, y ≤3,3% desde 2014. En 204 grupos todas las cifras son iguales (202 con `NUM_CON` distinto) y en 303 la IRA es igual. En el resto difieren. `NUM_CON` crece +1 entre semanas consecutivas en 86–89% de los pares en 2019–2022 (60–71% en 2012–2016); dentro de los grupos solo 312 de 827 tienen `NUM_CON` consecutivos, y 16 grupos repiten el mismo `NUM_CON`. Solo 92 grupos incluyen `ajuste = 7`. Diferencia anual entre suma y último reporte: 4,5% (2012), 2,9% (2013), 1,1% (2014), ≤0,6% desde 2015.
- **Inferencia:** `NUM_CON` funciona como contador de reportes por UPGD. **No es identificador de pacientes ni de casos.** No se sabe si un reporte posterior corrige, reemplaza o complementa al anterior.
- **Opciones:** sumar; último `NUM_CON`; conservar ambos y marcar; limitar a 2019–2022.
- **Evaluación:** sumar puede duplicar (filas idénticas); el último puede perder un complemento; limitar a 2019–2022 descarta siete años sin justificación suficiente y deja dos años en régimen 2020–2021.
- **Recomendación:** en las capas normalizada y validada conservar todas las filas (ya justificado). En la derivada y la analítica incluir **ambas variantes** (`suma` y `ultimo_reporte`), el número de reportes y un indicador de repetición. No elegir una hasta la respuesta del INS. En el entrenamiento, probar la sensibilidad a ambas.
- **Consecuencias:** V1/V2/V3 llevan dos columnas del indicador para 2012–2018; para 2019–2022 coinciden.
- **Estado: PENDIENTE (INS).** La parte de conservar filas y marcar es aprobable de inmediato.

### Decisión 3 — Suficiencia semanal
- **Qué se decide:** cuántos días diarios válidos se exigen para emitir un valor semanal.
- **Evidencia (hechos):** la regla de ≥6/7 reproduce 312/312 temperaturas del piloto; solo 2 semanas (Funes 2022 SE5 y SE52) quedaron NA. Es una regla del piloto, no de IDEAM. Con 6/7 las 12 estaciones de temperatura útiles superan el 80% de semanas; para precipitación, 53 estaciones superan 80% tanto con 6/7 como con 7/7.
- **Inferencia:** una suma con 6 días subestima el total sin avisar; mínimo, máximo y media son menos sensibles.
- **Recomendación:** ≥6/7 para mínima, máxima y media; 7/7 para la suma de lluvia. Guardar siempre `n_dias` y marcar `INSUFICIENTE`; no imputar ni interpolar.
- **Consecuencias:** V2 usa 6/7; V3 usa 7/7 en la suma. Es un parámetro versionado y se prueba la sensibilidad.
- **Estado: APROBABLE.** (La variante de lluvia no se usa hasta resolver la etiqueta, decisión pendiente en la sección 4.)

### Decisión 4 — Asignación estación→municipio
- **Qué se decide:** cómo vincular una estación puntual con un municipio.
- **Evidencia (hechos):** las estaciones se asignaron por nombre de municipio del catálogo; 99 estaciones en 44 municipios, 20 municipios sin ninguna. Solo 12 tienen temperatura ≥80% de semanas. Las altitudes de las estaciones con temperatura van de 1 a 3.141 m. La estación de Chachagüí es el aeropuerto de Pasto. No se dispone de altitud ni coordenadas de las cabeceras municipales.
- **Opciones:** solo estación propia; vecina por altitud o distancia; interpolación.
- **Evaluación:** vecina o interpolación requieren datos que no se tienen y una validación contra municipios con estación propia; hacerlo ahora sería suponer representatividad.
- **Recomendación:** solo estación propia con cobertura ≥80% de semanas (ya reflejada en V2), registrando código, altitud y estado de la estación en cada fila. El resto queda `SIN_ESTACION`.
- **Consecuencias:** V2: 12 municipios (11 sin Aldana, ver decisión 9). V3: 38 con precipitación. La representatividad (D-03) sigue siendo una limitación declarada.
- **Estado: CONDICIONAL.**

### Decisión 5 — Periodo de modelado
- **Evidencia (hechos):** total anual de IRA en Nariño: 54.738 (2019), 18.476 (2020), 23.038 (2021), 48.415 (2022). La mediana semanal por municipio-semana cae a 1 en 2020–2021. Las consultas totales cambiaron también (209.003 en 2020 frente a 376.424 en 2019).
- **Inferencia:** el quiebre refleja cambios de consulta y notificación; la causa no está documentada en los datos.
- **Opciones:** 2012–2022 completo; excluir 2020–2021; solo 2019–2022.
- **Recomendación:** el dataset analítico contiene 2012–2022 completo con una variable `regimen` (≤2019 / 2020–2021 / 2022). La exclusión se decide en el experimento, con comparación de resultados con y sin 2020–2021. No limitar a 2019–2022: pierde 7 años sin necesidad.
- **Consecuencias:** V1/V2/V3 incluyen todos los años. En entrenamiento, 2020–2021 se tratan como estrés o se excluyen explícitamente.
- **Estado: CONDICIONAL.**

### Decisión 6 — Año 2021
- **Evidencia (hechos):** `ACUMULADO` declara 1.048.576 filas, pero solo 219.207 tienen datos; 829.367 son filas vacías. Distribución semanal uniforme (3.875–4.363 filas por semana nacionales; 7.162 filas de Nariño frente a 7.503 en 2020 y 7.191 en 2022). 39 filas nacionales con semana 53 (0 en Nariño) en un año de 52 semanas. No hay conteo oficial.
- **Evaluación:** la hipótesis de truncamiento por el límite de Excel queda sin respaldo. Completitud no demostrada, pero tampoco hay señal de pérdida.
- **Recomendación:** incluir 2021 con la marca `completitud_no_verificada` y registrar las 39 filas de semana 53 como advertencia (las de Nariño: ninguna).
- **Consecuencias:** V1/V2/V3 incluyen 2021 con aviso. Puede excluirse en un experimento si el INS lo indica.
- **Estado: CONDICIONAL** (se cierra con la consulta del conteo oficial).

### Decisión 7 — Salto DANE 2017→2018
- **Evidencia (hechos):** total 0–4 de Nariño 126.835 → 134.253 (+5,85%); mediana por municipio +8,24%; 53 de 64 municipios suben más de 5%, 3 bajan más de 5%. Variaciones dentro de cada libro: mediana −0,19% (2016→2017) y −1,66% (2018→2019).
- **Inferencia:** el salto se debe al cambio de libro y de base de proyección; DANE no lo confirma en lo auditado.
- **Opciones:** dejar y marcar; reescalar; usar solo 2018+.
- **Recomendación:** dejar y marcar con `dane_libro`. Reescalar sin criterio DANE sería inventar una serie.
- **Consecuencias:** V1/V2/V3 incluyen `pob_0_4` y `dane_libro`. Cualquier tasa o modelo debe tratar la ruptura de forma explícita.
- **Estado: CONDICIONAL** (se cierra si DANE publica empalme).

### Decisión 8 — Calendario epidemiológico
- **Evidencia (hechos):** la regla documentada del primer domingo difiere 7 días de la regla del 4 de enero en 2013, 2014, 2018, 2019 y 2020. Las únicas semanas 53 en los libros SIVIGILA son las de 2014 y 2020, lo que coincide con la regla del 4 de enero. El piloto se verificó contra boletines INS solo para 2016 y 2022.
- **Inferencia:** la regla del 4 de enero es probablemente la que corresponde; no está contrastada con un calendario oficial por año.
- **Recomendación:** calendario como tabla de referencia versionada por año, con fuente. Usar la regla del 4 de enero como borrador, marcada `calendar_verificado = NO` en los años sin confirmación, y no calcular el valor semanal de IDEAM en un año sin calendario confirmado.
- **Consecuencias:** afecta V2 y V3 (agregación de IDEAM); V1 usa la semana reportada por SIVIGILA, pero necesita el calendario para las fechas. 2016 y 2022 pueden marcarse como verificados.
- **Estado: CONDICIONAL.**

### Decisión 9 — Estación de Aldana (52055230)
- **Evidencia (hechos):** `TSSM_MN_D` = `TSSM_MX_D` en 4.016 de 4.016 días y `TSSM_MEDIA_D` > máxima en los mismos 4.016 días. Es la única de las 22 estaciones con esa anomalía.
- **Recomendación:** excluir mínima y máxima de esta estación (estado `SERIE_NO_CONFIABLE`). La media tampoco puede verificarse coherente con ellas; se sugiere excluir las tres hasta la aclaración de IDEAM, lo que deja Aldana sin temperatura en V2.
- **Consecuencias:** V2: 11 municipios y 5.724 municipio-semanas sin Aldana. V3: la precipitación de Aldana no se ve afectada por esta anomalía.
- **Estado: APROBABLE** (consulta a IDEAM para reincorporar).

### Decisión 10 — Nombre del indicador
- **Evidencia (hechos):** el piloto usa `..._consultations` (v1) y `..._patient_count` (v2); los documentos usan "atenciones". El nombre "pacientes" no está respaldado y "consultas" tampoco está confirmado. El nombre `ira_ce_urg_0_4_notificado` que propuse antes presupone "consulta externa y urgencias", cuyo alcance es inferido.
- **Recomendación:** `iracext_0_4_notificado`, que solo afirma el campo de origen y que es un conteo notificado. Ajustar cuando el INS aclare.
- **Consecuencias:** V1/V2/V3 usan el mismo nombre; los CSV del piloto quedan sin cambios.
- **Estado: APROBABLE.**

### Decisión 11 — Consultas institucionales
- **Qué se decide:** enviar o no las preguntas.
- **Recomendación:** enviarlas. Resuelven las decisiones 2, 3 (lluvia), 6, 7 y 8.
- **Estado: APROBABLE**; la acción es suya (no se envió nada). Texto sugerido en la sección 6.

### Decisión 12 — Conservar los scripts de análisis
- **Hecho:** los scripts están en el directorio temporal de la sesión, fuera del repositorio.
- **Recomendación:** conservarlos en `data/scripts/` para reproducibilidad.
- **Estado: PENDIENTE de su autorización.** No se movió ni se copió ningún archivo en esta tarea.

---

## 3. Decisiones que pueden aprobarse de inmediato

- **3** (≥6/7 en temperatura; 7/7 para suma de lluvia).
- **9** (excluir la estación de Aldana).
- **10** (nombre `iracext_0_4_notificado`).
- **11** (enviar las consultas).
- La parte sin riesgo de la **2**: conservar todas las filas y marcar los grupos repetidos.

## 4. Decisiones que requieren confirmación institucional

- **2** (INS): significado de los reportes repetidos y de `NUM_CON`.
- **1** (INS): significado de `totcext_*` y del conteo; define si la proporción es válida.
- **6** (INS): conteo oficial de 2021 y las 39 filas con semana 53.
- **7** (DANE): empalme de las dos series.
- **8** (INS): calendario oficial por año.
- **Precipitación** (IDEAM): sufijo `_INTER`, que bloquea V3 y la parte lluvia de la decisión 3.
- **4 y 9** (IDEAM): representatividad de estaciones y estación de Aldana.

## 5. Reglas recomendadas por versión

**V1 — Epidemiología + población (64 municipios, 2012–2022; malla de 36.736 filas, 34.224 con IRA completa)**
- Todas las filas de SIVIGILA conservadas; semanas sin fila = `AUSENTE` (nunca 0); vacíos en `iracext_*` = NULL, con la bandera `PARCIAL_VACIOS`.
- Dos variantes del indicador (suma y último `NUM_CON`) más número de reportes.
- Conteo `iracext_0_4_notificado` y proporción sobre `totcext_1..3` (marcada pendiente).
- Población 0–4 con `dane_libro`; sin tasas ni "incidencia".
- Años 2020–2021 con `regimen`; 2021 con `completitud_no_verificada`.
- Código y departamento notificador cruzados; las 10 filas incongruentes marcadas, no corregidas.
- Calendario versionado; filas fuente con archivo, hoja, fila y hash.

**V2 — V1 + temperatura (11 municipios tras excluir Aldana; 5.724 municipio-semanas con IRA completa y temperatura)**
- Solo estación propia con cobertura ≥80% de semanas; ≥6/7 días; guardar `n_dias`, código, altitud y estado de la estación.
- Resto de municipios `SIN_ESTACION`; sin vecinas ni interpolación.
- Estación de Aldana excluida (`SERIE_NO_CONFIABLE`).
- Solo años con calendario verificado o marcados `calendar_verificado = NO`.
- Limitación declarada: representatividad no evaluada; muestra dominada por Pasto y Tumaco.

**V3 — V2 + precipitación (38 municipios, 19.934 municipio-semanas; sujeto a confirmación)**
- Se construye solo después de que IDEAM confirme etiqueta y unidad de `PTPM_CON_INTER`.
- Suma semanal con 7/7 días; `n_dias_prec_gt135` como alerta, sin eliminar valores.
- Misma regla de estación propia.

**Para todas:** sin datos sintéticos; sin imputación; la ausencia no es cero; cada versión conserva los identificadores y no sobrescribe la anterior.

## 6. Preguntas concretas para INS, IDEAM y DANE

**INS / Secretaría de Salud de Nariño (evento 995)**
1. Cuando una UPGD envía más de un reporte para la misma semana, ¿el de mayor `NUM_CON` reemplaza, corrige o complementa al anterior?
2. ¿Por qué hay filas con el mismo `NUM_CON` en el mismo prestador y semana (16 grupos en Nariño en 2015, 2016 y 2018)?
3. ¿Qué significa `ajuste = 7` en este evento y cómo debe tratarse?
4. ¿`totcext_1..3` son las consultas externas y urgencias totales (todas las causas) de los grupos <1, 1 y 2–4 años? ¿`iracext_*` cuenta consultas, atenciones o pacientes?
5. ¿Las semanas sin fila (Chachagüí SE44 y SE52 y Funes SE11 y SE21 de 2016; Francisco Pizarro casi todo 2020) significan no notificación, archivo no entregado o cero?
6. ¿Cuál es el conteo oficial de registros del evento 995 en 2021, y qué son las 39 filas con semana 53 en 2021?
7. ¿Hay un calendario epidemiológico oficial por año 2012–2023 (inicio y fin de cada semana, y años de 53 semanas)?
8. ¿Cambió la definición o el formulario del evento entre 2012 ("IRAG" en el nombre del evento) y 2016–2022, y hay cambios de notificación en 2014 y 2020–2021?

**IDEAM**
1. ¿Qué es `PTPM_CON_INTER` y cuál es su unidad? ¿Equivale a `PTPM_CON`?
2. ¿Existen banderas de calidad y nivel de aprobación de las series diarias de temperatura y precipitación?
3. En la estación 52055230 (Aldana), `TSSM_MN_D` y `TSSM_MX_D` son idénticas todos los días y la media es mayor que la máxima: ¿qué ocurre y existe una versión corregida?
4. ¿El valor sellado con fecha D a las 07:00 corresponde al acumulado de D−1→D o de D→D+1?
5. ¿Qué criterio recomienda IDEAM para usar una estación como representativa de un municipio?

**DANE**
1. ¿Existe un empalme oficial entre las proyecciones municipales 2005–2017 y 2018–2042, y explica el salto de 2017 a 2018?
2. ¿Cómo debe tratarse la población 0–4 de municipios pequeños (<500) para tasas?
3. ¿Habrá nuevas revisiones de la serie 2018–2042 posteriores a julio de 2025?

---

*Fin del documento. No se ejecutó ninguna fase posterior.*
