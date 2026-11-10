# Consulta al IDEAM — Series diarias de temperatura y precipitación (Nariño)

> **BORRADOR PARA REVISIÓN. NO ENVIADO.** Requiere revisión y autorización de la autora antes de cualquier envío. No hay respuesta del IDEAM: lo marcado como «pendiente» no está confirmado.

**Fecha del borrador:** 5 de noviembre de 2026
**Proyecto:** RESPIRA — análisis de infecciones respiratorias agudas en menores de cinco años, Nariño
**Remitente:** [nombre y datos de contacto de la autora — completar antes del envío]
**Destinatario sugerido:** IDEAM — grupo de datos hidrometeorológicos / atención al ciudadano (a confirmar)

## 1. Contexto

Usamos las extracciones nacionales de series diarias (`PrecipitacionNacionalDiaria`, `TemperaturaNacionalDiaria`, `MetereologiaNacionalDiaria`), archivos `{VARIABLE}@{CÓDIGO}.data` con columnas `Fecha|Valor`, y el catálogo nacional de estaciones, para agregar temperatura y precipitación por semana epidemiológica en municipios de Nariño (2012–2022). Revisamos 99 estaciones candidatas de Nariño. Los archivos no incluyen unidad, bandera de calidad ni nivel de aprobación; las dos fuentes oficiales que consultamos son el Manual GDI-M005 v2 y la respuesta al radicado 20259050026354_SM.

## 2. Preguntas

### Tema A — Precipitación `PTPM_CON_INTER`

**Antecedente.** El manual GDI-M005 documenta `PTPM_CON` (milímetros, día pluviométrico 07:00–07:00). Las series locales se llaman `PTPM_CON_INTER`.

1. **A1.** ¿Qué significa el sufijo `_INTER`? ¿`PTPM_CON_INTER` equivale a `PTPM_CON`? *Por qué:* no usamos precipitación hasta aclararlo.
2. **A2.** ¿Cuál es la unidad del valor (mm)?
3. **A3.** El archivo estampa cada día a las 07:00:00. El valor de la fecha D, ¿es el acumulado de D−1 07:00 a D 07:00 o de D 07:00 a D+1 07:00? *Por qué:* define a qué semana epidemiológica pertenece el valor en los bordes.
4. **A4.** ¿Un valor 0,0 es «sin lluvia medida» y la ausencia de registro es «no medido»? (Hay 127 días con más de 135 mm en 2012–2022 en estas estaciones; no los eliminamos.)

### Tema B — Calidad y aprobación

5. **B1.** ¿Existen banderas de calidad y nivel de aprobación (preliminar/definitivo) para las series diarias de `TSSM_MN_D`, `TSSM_MX_D`, `TSSM_MEDIA_D` y `PTPM_CON_INTER`? ¿Se pueden entregar con los datos? *Por qué:* hoy no podemos distinguir un dato validado de uno preliminar.
6. **B2.** ¿Los datos de 2012–2022 que descargamos están en versión definitiva? Los valores recientes, ¿pueden cambiar?
7. **B3.** ¿Cómo se calculan `TSSM_MN_D`, `TSSM_MX_D` y `TSSM_MEDIA_D` exactamente (¿termómetros de extremas, tres lecturas diarias, otra)? ¿El cálculo exige las tres lecturas del día? *Por qué:* la media diaria tiene decimales largos que sugieren un promedio de varias lecturas.
8. **B4.** ¿Qué criterio oficial existe para valores negativos o atípicos? La segunda auditoría detectó algunos negativos en el historial completo de ciertas series (no en 2012–2022 de las series evaluadas ahora). No eliminamos nada hasta tener criterio oficial.

### Tema C — Estación de Aldana (código 52055230, «Aeropuerto San Luis – Aut»)

**Antecedente.** En 2012–2022 la serie `TSSM_MN_D` es **idéntica** a `TSSM_MX_D` en los 4.016 días con datos, y `TSSM_MEDIA_D` es mayor que ambas en esos mismos 4.016 días (la media diaria es más alta que la máxima). En las otras 21 estaciones de temperatura esto no ocurre.

9. **C1.** ¿Cuál es la explicación (error de carga, variable mal etiquetada, otro tipo de sensor)? ¿Existe una versión corregida? *Por qué:* hemos excluido las tres variables de temperatura de esta estación hasta aclararlo.

### Tema D — Ubicación y representatividad de estaciones

**Antecedente.** Asignamos estaciones a municipios por coincidencia del campo «Municipio» del catálogo. Esto no demuestra la ubicación geográfica ni la representatividad.

10. **D1.** La estación 52045020 «Aeropuerto Antonio Nariño» figura en el catálogo en el municipio de **Chachagüí** (lat 1,394083, lon −77,290861, 1.796 m). ¿Confirma IDEAM que está físicamente en ese municipio? *Por qué:* nuestra regla solo usa estaciones del mismo municipio y esta es la única de los tres municipios del piloto que genera dudas.
11. **D2.** Para los municipios de Nariño con estación de temperatura (Pasto, Aldana, Chachagüí, Funes, Puerres, Pupiales, Samaniego, San Bernardo, Taminango, Tangua, Tumaco, Túquerres), ¿qué criterio recomienda IDEAM para considerar que la estación representa al municipio, dada la gran diferencia de altitud (de 1 a 3.141 m)?
12. **D3.** ¿Recomienda IDEAM usar la estación de un municipio vecino o interpolar para municipios sin estación? Si es así, ¿con qué criterio de distancia y altitud? (Hoy no lo hacemos.)

### Tema E — Catálogo de estaciones

13. **E1.** El catálogo nacional en CSV tiene 19.828 filas pero 9.914 códigos únicos: cada estación aparece dos veces idéntica. ¿Es esperado? ¿Cuál es la edición vigente (CSV, CNE `.xls` con 4.522 estaciones, archivo de Nariño con 168 códigos)?
14. **E2.** La estación 52040030 «CHACHAGUI» figura con altitud de 20 m, pero está a unos 3 km de una estación a 1.796 m. ¿El valor es correcto?
15. **E3.** ¿Qué indica «En Mantenimiento» para estaciones como 51025090 (Granja El Mira, Tumaco) y 52055030 (Bombona, Consacá), que tienen datos recientes?

### Tema F — Otras variables (no se usarán de inmediato)

16. **F1.** ¿Qué son y qué unidad tienen `HR_CAL_MEDIA_D`, `TPR_CAL` y `TV_CAL`? Asumimos que `HR_CAL_MEDIA_D` es humedad relativa media pero no lo hemos confirmado.

### Tema G — Procedencia de las extracciones

17. **G1.** Las carpetas de series diarias se obtuvieron de los enlaces oficiales de descarga masiva. ¿Qué fecha y versión corresponden a cada una? ¿Existe un hash o un listado oficial de archivos? *Por qué:* para poder demostrar de qué entrega proviene cada dato.

## 3. Formato de respuesta solicitado

Una respuesta por numeral con el documento oficial que la respalda. Si algún punto no puede contestarse, indíquenlo para registrarlo como limitación.

## 4. Antecedentes disponibles

`reports/quinta_auditoria/INFORME_GENERAL.md` (sección 2) y `EVALUACION_ESTACIONES_IDEAM.csv`.
