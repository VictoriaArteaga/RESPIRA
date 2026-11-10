# Consulta al Instituto Nacional de Salud (INS) y a la Secretaría de Salud de Nariño — Evento 995

> **BORRADOR PARA REVISIÓN. NO ENVIADO.** Requiere revisión y autorización de la autora antes de cualquier envío. No hay respuesta de la entidad: nada de lo aquí descrito como «pendiente» ha sido confirmado.

**Fecha del borrador:** 5 de noviembre de 2026
**Proyecto:** RESPIRA — análisis de infecciones respiratorias agudas (IRA) en menores de cinco años, departamento de Nariño
**Remitente:** [nombre y datos de contacto de la autora — completar antes del envío]
**Destinatarios sugeridos:** INS (Dirección de Vigilancia y Análisis del Riesgo en Salud Pública, equipo SIVIGILA / IRA) y Secretaría de Salud de Nariño (vigilancia epidemiológica) — a confirmar

## 1. Contexto

Estamos construyendo, con fines académicos y de análisis exploratorio, un conjunto de datos semanal por municipio con la notificación colectiva del evento 995 (morbilidad por IRA), años 2012–2022, para los 64 municipios de Nariño. Trabajamos con los libros anuales `Datos_{año}_995.xlsx` (hojas de detalle). **No calculamos incidencia**: usamos el conteo de lo notificado y queremos asegurarnos de interpretarlo correctamente.

Campo de interés: `iracext_1 + iracext_2 + iracext_3` (grupos de edad 1, 2 y 3, que entendemos como <1 año, 1 año y 2–4 años según la estructura de registros del INS de 2016). Otros campos relevantes: `num_con`, `cod_pre`, `cod_sub`, `ajuste`, `fec_aju`, `totcext_1..3`, `semana`, `año`.

## 2. Preguntas

### Tema A — Reportes repetidos de una misma UPGD en la misma semana

**Antecedente.** En los libros de Nariño hay 827 combinaciones de municipio–año–semana–UPGD–sede con más de una fila (1.705 filas), todas entre 2012 y 2018 (225 en 2012, 287 en 2013, 119 en 2014, 45 en 2015, 74 en 2016, 32 en 2017 y 45 en 2018); no hay ninguna en 2019–2022. En 204 de ellas todas las cifras coinciden; en el resto difieren. Ejemplo: Chachagüí, 2016, semana 43, UPGD `5224001399` sede `01`, `num_con` 263 y 264, con valores de IRACEXT 4/0/4 y 0/0/1.

1. **A1.** Cuando una UPGD envía más de un reporte para la misma semana epidemiológica y evento, ¿el reporte con mayor `num_con` **reemplaza**, **corrige** o **complementa** (se suma) al anterior? *Por qué:* determina si el conteo semanal debe sumar las filas o tomar la última; hoy conservamos ambas posibilidades sin elegir.
2. **A2.** ¿Existen reglas oficiales de consolidación para extracciones históricas 2012–2018 que puedan diferir de las de 2019–2022?
3. **A3.** ¿Por qué no aparecen repeticiones desde 2019? ¿Cambió el sistema, el proceso de depuración o la forma de entregar los datos? *Por qué:* la regla de 2012–2018 puede no aplicar a años posteriores.
4. **A4.** En 16 grupos de Nariño (2 en 2015, 12 en 2016, 2 en 2018) el **mismo `num_con` aparece en dos o más filas** de la misma UPGD y semana. ¿Qué significa? ¿Es una duplicación de carga? *Por qué:* según nuestra lectura, `num_con` es el consecutivo de reporte de la UPGD, de modo que un mismo número en dos filas sería inesperado.
5. **A5.** Confirmen que `num_con` es un consecutivo de reportes de la UPGD y **no** identifica pacientes ni casos. *Por qué:* nuestra lectura se basa en el anexo de estructura de registros 2016; en los datos sube +1 entre semanas consecutivas en la mayoría de los pares.

### Tema B — Campo `ajuste` y `fec_aju`

**Antecedente.** En Nariño `ajuste` solo toma los valores 0 y 7 (el 7 aparece en 3 a 139 filas por año).

6. **B1.** ¿Qué significa `ajuste = 7` en el evento 995 colectivo? ¿Implica que esa fila reemplaza otra? *Por qué:* solo 92 de los 827 grupos repetidos contienen una fila con ajuste 7; queremos saber si el ajuste debe afectar el conteo.
7. **B2.** ¿`fec_aju` es la fecha de ajuste de ese registro?

### Tema C — Significado de los campos de conteo

8. **C1.** ¿`iracext_1..3` cuenta **consultas externas y de urgencias** (atenciones), **pacientes** distintos o ambos? ¿Pueden contarse varias veces una misma persona? *Por qué:* hoy el indicador se llama `iracext_0_4_notificado` y evitamos las palabras «pacientes» o «casos» hasta que ustedes lo aclaren.
9. **C2.** ¿`totcext_1..3` son el **total de consultas externas y urgencias por todas las causas** en los mismos grupos de edad que `iracext_1..3`? ¿Es válido usarlos como denominador de una proporción? *Por qué:* queremos ofrecer, además del conteo, la proporción de consultas por IRA, que controla las diferencias de volumen de reporte.
10. **C3.** ¿`tot_iraext` y `tot_exturg` son la suma de los siete grupos de edad? (No existen en el libro de 2012.)
11. **C4.** El nombre del evento es «MORBILIDAD POR IRAG» en las primeras filas de 2012 y «MORBILIDAD POR IRA» en 2016–2022. ¿Cambió la definición, el formulario o el alcance del evento 995 entre 2012 y 2016?
12. **C5.** ¿Hubo cambios de formulario o de notificación en 2014 (el total de consultas de 0–4 años en Nariño pasa de 346.292 en 2013 a 492.530 en 2014) o en 2020–2021 (el conteo de IRA cae de 54.738 en 2019 a 18.476 en 2020 y 23.038 en 2021)? *Por qué:* para separar cambios de notificación de cambios de la enfermedad.
13. **C6.** Algunas filas tienen celdas vacías (no cero) en `iracext_*` (por ejemplo 155 filas en 2013, 34 en 2016, 38 en 2018). ¿Un vacío significa «no reportado», «cero» o «error de captura»? *Por qué:* nosotros los conservamos como vacíos y no los convertimos en cero.

### Tema D — Semanas sin registro

**Antecedente.** Hay semanas en que un municipio no tiene ninguna fila: Chachagüí en las semanas 44 y 52 de 2016 y Funes en las semanas 11 y 21 de 2016; Francisco Pizarro tiene filas en una sola semana de 2020.

14. **D1.** Una semana sin fila para un municipio, ¿significa que no hubo notificación (UPGD no reportó), que el municipio no tuvo casos que reportar, o que el dato no llegó a la extracción?
15. **D2.** ¿Pueden entregarnos la lista de UPGD activas por municipio y año, o la de reportes esperados? *Por qué:* permitiría distinguir ausencia de reporte de ausencia de enfermedad.

### Tema E — Integridad del libro 2021

**Antecedente.** El libro `Datos_2021_995.xlsx` (hoja `ACUMULADO`) declara 1.048.576 filas, pero solo 219.207 tienen datos; las restantes están vacías. La distribución por semana es regular. Nariño tiene 7.162 filas. No tenemos un conteo oficial.

16. **E1.** ¿Cuál es el número oficial de registros del evento 995 de 2021 (nacional y de Nariño)? *Por qué:* para confirmar que la extracción está completa.
17. **E2.** El libro de 2021 contiene 39 filas nacionales con `semana = 53` y `año = 2021`, y 2021 tiene 52 semanas epidemiológicas. ¿A qué corresponden?

### Tema F — Calendario epidemiológico

18. **F1.** ¿Pueden facilitarnos el calendario epidemiológico oficial de cada año 2012–2023 (fecha de inicio y fin de cada semana y número de semanas)? *Por qué:* hoy aplicamos una regla (la semana 1 contiene el 4 de enero) que concuerda con las semanas 53 que aparecen en 2014 y 2020, pero solo la comprobamos contra boletines del INS para 2016 y 2022.
19. **F2.** ¿Es correcto que 2014 y 2020 tuvieron 53 semanas epidemiológicas?

### Tema G — Códigos y municipio notificador

20. **G1.** `cod_mun` ¿corresponde siempre al municipio de la UPGD notificadora y no al de residencia del paciente? *Por qué:* el denominador demográfico es la población del municipio.
21. **G2.** Hay filas con código incongruente respecto del departamento notificador: 2 filas de 2012 con código 52838 (Túquerres) y departamento BOYACÁ (Tununguá), 7 filas de 2014 con código 52356 (Ipiales) y departamento BOGOTÁ, y 1 fila de 2012 con código 52000. ¿Cuál es el código correcto y deben corregirse en la fuente?
22. **G3.** ¿Existen cambios de código de UPGD o de municipio entre años (el formato de `cod_pre` y `cod_sub` varía: con y sin ceros iniciales)?

### Tema H — Uso del conteo para tasas

23. **H1.** ¿Qué denominador recomienda el INS para expresar este conteo como tasa o proporción (población DANE 0–4, consultas totales, población afiliada, otra)? ¿Se recomienda **no** calcular tasas con este evento? *Por qué:* hasta que el INS lo valide no calcularemos tasas ni lo llamaremos incidencia.

## 3. Formato de respuesta solicitado

Una respuesta por numeral (A1, A2, …), indicando el documento oficial que la respalda, cuando exista. Si algún punto no puede responderse, indíquenlo para poder registrarlo como limitación.

## 4. Antecedentes disponibles

Informe de la quinta auditoría (`reports/quinta_auditoria/INFORME_GENERAL.md`, secciones 3.3–3.5) y `EVALUACION_VARIABLES_SIVIGILA.csv`. No se adjuntan datos con identificadores de personas; los libros contienen campos de contacto que no hemos copiado ni analizado.
