# Viabilidad de enfoques de predicción con los datos disponibles

**Fecha:** 5 de noviembre de 2026. No se implementó ni entrenó ningún modelo. Los conteos de observaciones se obtuvieron contando municipio-semanas con datos completos en los originales; no son resultados de modelado.

> **Advertencia.** Ningún escenario se declara viable «para producción». Para eso faltan, como mínimo: (1) un modelo base simple contra el cual comparar, (2) validación temporal con datos tal como estarían disponibles en el momento de predecir, (3) resolución de las reglas de reporte repetido y de los vacíos, y (4) confirmación del significado del indicador. Aquí se evalúa solo **qué es posible intentar** y **con qué riesgos**.

## 1. Conceptos comunes a los tres escenarios

**Unidad de observación:** municipio × semana epidemiológica.
**Periodo posible:** 2012–2022 (574 semanas), con el calendario de 53 semanas en 2014 y 2020.
**Numerador disponible:** `iracext_1 + iracext_2 + iracext_3` (IRA consulta externa/urgencias, 0–4 años), sin consolidar reportes repetidos (2012–2018) y con vacíos en 2013, 2014, 2016, 2017 y 2018.
**Denominadores posibles:** consultas totales de 0–4 años (`totcext_1..3`, pendiente de validar) y población 0–4 anual (DANE).

**Posibles variables objetivo** (a decidir; ver decisión 1 de `INFORME_GENERAL.md`):

| Objetivo | Ventajas | Problemas |
|---|---|---|
| Conteo semanal | Es lo que hay; sin transformaciones | Mediana semanal <10 en 46 de 64 municipios y <3 en 14 (sin 2020–2021); 12,5% de ceros en los 12 municipios con temperatura (17,1% en los 64); mezcla enfermedad y volumen de reporte |
| Proporción IRA / consultas totales | Controla el volumen de reporte | `totcext_*` sin validar; varía de 0,26 (2012) a 0,04 (2020) |
| Tasa por población 0–4 | Comparable entre municipios | Tasas implícitas de 0,16–0,66 por niño-año en el piloto (demasiado bajas para incidencia); salto DANE 2018; municipios con <500 niños |
| Clase de alerta (por encima de un umbral histórico) | Más robusta a conteos bajos | El umbral debe definirse sin usar el periodo de prueba; no hay definición aprobada |

**Hechos que condicionan cualquier modelo:**

- **Quiebre 2020–2021:** el conteo anual de Nariño pasa de 54.738 (2019) a 18.476 (2020) y 23.038 (2021), y a 48.415 (2022); la mediana semanal por municipio-semana cae a 1. No es solo estacionalidad: cambia el régimen de consulta y de notificación.
- **Cambios de volumen de reporte:** las consultas totales de 0–4 años pasan de 346.292 (2013) a 492.530 (2014).
- **Concentración:** Pasto (mediana semanal ≈340 en 2019/2022) y Tumaco (≈108) dominan la suma; el resto de los 12 municipios con temperatura tiene medianas de 1 a 10.
- **Las cifras de SIVIGILA son versiones finales:** el reporte original, los ajustes (`ajuste`, `fec_aju`) y reportes repetidos posteriores ya están incorporados. En el momento real de predecir, esas versiones no existen.

## 2. Escenario 1 — Solo variables epidemiológicas

| Aspecto | Evaluación |
|---|---|
| Variables de entrada | Rezagos y estadísticos móviles del propio conteo (o proporción) por municipio; semana epidemiológica (estacionalidad); opcionalmente, `totcext_*` de semanas previas y un indicador de reporte repetido/vacío |
| Objetivo | Conteo, proporción o alerta en la semana t+h |
| Cobertura temporal | 2012–2022 |
| Cobertura municipal | 64/64 municipios, con distinta calidad (68,6%–99,7% de semanas con fila; 34 con ≥95%) |
| Observaciones potenciales | 34.224 municipio-semanas con IRA completa (de 36.736 posibles); 29.586 con 4 semanas previas completas. Por periodo (con 4 rezagos): 2012–2018: 17.972; 2019: 3.014; 2020–2021: 5.541; 2022: 3.059 |
| Limitaciones | Los municipios pequeños tienen conteos casi aleatorios; vacíos en numeradores (2013: 155 filas); reportes repetidos en 2012–2018; régimen 2020–2021; 2012 con menos reporte (2.503 municipio-semanas con datos frente a ≈3.200 en años siguientes) |
| Fuga temporal | Alta si se usa partición aleatoria (semanas vecinas casi idénticas); si los rezagos se calculan con la regla de consolidación elegida con información posterior; si se normaliza o se define el umbral de alerta con el conjunto completo; datos finales en lugar de «tal como se conocían» |
| Validación temporal | **Posible.** Origen rodante: entrenar 2012–2018 → validar 2019 → probar 2022 (el periodo 2020–2021 se trata aparte como estrés). Con 3 municipios y 2 años del piloto **no** es posible |
| Predicción de semanas futuras | **Viable de explorar** (horizonte 1–4 semanas). Es el único escenario con cobertura nacional del departamento. Debe compararse con modelos de referencia: «misma semana del año anterior», media móvil, y un modelo estacional simple |

## 3. Escenario 2 — Epidemiología + meteorología

| Aspecto | Evaluación |
|---|---|
| Variables de entrada | Las del escenario 1 más temperatura mínima, máxima y media semanales **observadas con rezago** (t−1, t−2…), y (condicionado) precipitación semanal |
| Cobertura temporal | 2012–2022 |
| Cobertura municipal | **12 municipios** con temperatura (11 si se excluye Aldana por su anomalía de min/máx); **38** con precipitación (etiqueta `PTPM_CON_INTER` sin confirmar) |
| Observaciones potenciales | Temperatura: **6.282** municipio-semanas con IRA completa y las tres temperaturas con ≥6/7 días (5.110 si se excluyen 2020–2021; 5.724 sin Aldana); 5.612 con 4 rezagos del indicador. Por periodo con rezagos: 2012–2018: 3.395; 2019: 583; 2020–2021: 1.074; 2022: 560. Temperatura y precipitación a la vez: 6.273 en los mismos 12 municipios. Precipitación sola: 19.934 en 38 municipios |
| Limitaciones | Estación puntual ≠ municipio (altitudes de 1 a 3.141 m); 52 municipios sin temperatura; sin banderas de calidad IDEAM; muestra dominada por Pasto y Tumaco; sin estación en el 31% de los municipios para ninguna variable; 2012–2013 con menos observaciones con rezagos (322 y 317) |
| Fuga temporal | La temperatura de la propia semana t no estará disponible al predecir t+h salvo que se usen pronósticos meteorológicos (que no están en los datos); solo son legítimos rezagos observados. La selección de estaciones y de umbrales de cobertura con el periodo completo es otra fuga leve. El valor semanal usa 6/7 días: si la semana no ha terminado, ese valor no existe |
| Validación temporal | Posible con las mismas particiones; 560 observaciones en la prueba de 2022 (12 municipios) |
| Predicción de semanas futuras | **Viable de explorar solo en los municipios con estación.** Lo que se podría aprender es limitado: la relación entre temperatura y consultas por IRA no está demostrada con estos datos; podría resultar nula, y esa también es una conclusión válida |

## 4. Escenario 3 — Epidemiología + meteorología + demografía

| Aspecto | Evaluación |
|---|---|
| Variables de entrada | Las del escenario 2 más población 0–4 (como tamaño de población o *offset* en un modelo de conteos) y, si se aprueba, una tasa |
| Cobertura | Igual al escenario 2 (DANE cubre 64/64 y 2012–2022 sin vacíos; no restringe) |
| Observaciones potenciales | Las mismas que el escenario 2 (6.282; 5.612 con rezagos) |
| Limitaciones | La población es constante en el año y casi constante entre años dentro de un libro, así que dentro de un municipio **no aporta variación**; aporta tamaño entre municipios. Salto 2017→2018 (mediana +8,2%): coincide con el cambio de libro, de modo que un modelo puede usar la población como sustituto del periodo. Municipios con <500 niños |
| Fuga temporal | La proyección del libro 2018–2042 está actualizada a julio de 2025: contiene información posterior a las semanas que se pretende predecir (ligera, pero real) |
| Validación temporal | Igual que el escenario 2 |
| Predicción de semanas futuras | Viable de explorar. Valor añadido sobre el escenario 2: tratar el tamaño de población como *offset*; no se espera que mejore el poder predictivo dentro de municipio |

## 5. Comparación

| Criterio | E1 Epi | E2 Epi+meteo | E3 Epi+meteo+demografía |
|---|---|---|---|
| Municipios | 64 | 12 (temp.) / 38 (precip., condicionado) | 12 / 38 |
| Municipio-semanas | 34.224 | 6.282 / 19.934 | 6.282 / 19.934 |
| Con 4 rezagos | 29.586 | 5.612 | 5.612 |
| Prueba 2022 (con rezagos) | 3.059 | 560 | 560 |
| Riesgo principal | Régimen 2020–2021; versiones finales | Representatividad de estación; muestra pequeña y concentrada | Salto DANE como proxy de periodo |
| Dependencia de decisiones pendientes | Regla de repetición, indicador | + calendario, suficiencia semanal, asignación de estación | + denominador |
| Valor esperado | Línea base de referencia | Prueba de si el clima aporta | Normalización entre municipios |
| ¿Se puede explorar ya? | Sí, tras decidir regla de repetición y vacíos | Sí, tras aprobar asignación y suficiencia | Sí, tras aprobar denominador |
| ¿Para producción? | **No comprobado** | **No comprobado** | **No comprobado** |

## 6. Riesgos de fuga transversales

1. **Partición aleatoria** de semanas: prohibida; usar bloques temporales.
2. **Versiones finales vs tiempo real:** el modelo puede estar sobrevalorado porque entrena y se evalúa con reportes ya consolidados. Una prueba honesta requeriría las versiones tal como se recibían (se desconocen: `fec_not` y `fec_aju` ayudan, pero los libros son acumulados).
3. **Reglas elegidas mirando los resultados:** umbral de cobertura, estación asignada, consolidación de repetidos; se deben fijar antes de ver el conjunto de prueba.
4. **Normalización o umbral de alerta con todo el periodo.**
5. **Rezagos que cruzan años** en un piloto de 2016 y 2022 (no contiguos): inválido.
6. **Identidad del municipio** como predictor en un modelo conjunto: con Pasto y Tumaco dominando, puede aprender el nivel por municipio y no la dinámica.
7. **Población del libro actualizado** como señal de periodo.
8. **Cambios de notificación** (2014, 2020–2021) como señal confundida con enfermedad.

## 7. Qué comprobar antes de considerar un modelo útil

- Línea base: «misma semana del año anterior» y un modelo estacional simple, por municipio.
- Métrica por municipio y por régimen (≤2019, 2020–2021, 2022), no solo global.
- Intervalos de incertidumbre calibrados (conteos pequeños).
- Prueba con y sin Pasto/Tumaco.
- Sensibilidad a las reglas pendientes (sumar vs último reporte vs conservar ambos), a la suficiencia semanal (6/7 vs 7/7) y a la exclusión de 2020–2021.
- Prueba de *nowcasting* realista si el objetivo es operar con reportes parciales de la semana más reciente.
- Declaración explícita de qué municipios quedan fuera por falta de estación.

## 8. Conclusión de viabilidad

- **Con los datos actuales sí es posible** diseñar un **primer experimento exploratorio de pronóstico semanal a 1–4 semanas**, empezando por el escenario 1 en los 64 municipios y añadiendo meteorología en los 12 con temperatura.
- **No es posible** afirmar que el modelo sea útil ni confiable; para ello faltan las comprobaciones de la sección 7 y las respuestas a las consultas con INS/IDEAM.
- **No es defendible** entrenar con el piloto actual (312 filas, 2 años no contiguos).
