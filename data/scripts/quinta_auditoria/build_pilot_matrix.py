import pandas as pd
R = "C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
OUT = R + "reports/quinta_auditoria/"
V = 'Verificada'
U = 'Utilizable con restricciones'
P = 'Pendiente de validación'
N = 'No utilizable actualmente'
pil = []


def a(var, ver, fuente, transf, calidad, clase, obs, evid):
    pil.append(dict(variable=var, presente_en=ver, fuente=fuente, transformacion=transf, calidad=calidad,
                    clasificacion=clase, observaciones=obs, verificacion_5a_auditoria=evid))


a('municipality_divipola', 'v1 y v2', 'SIVIGILA cod_mun; DANE MPIO',
  'Normalizado a código de 5 dígitos; guardado como entero', '3 códigos válidos (52240, 52287, 52678), presentes en DANE y en el catálogo IDEAM', V,
  'Es municipio NOTIFICADOR, no de residencia. Como entero no conserva ceros iniciales (irrelevante para Nariño, relevante para otros departamentos).',
  'Coincide con la clave de los 312 registros recalculados desde SIVIGILA 2016/2022')
a('municipality_name', 'v1 y v2', 'DANE / catálogo IDEAM', 'Texto con tildes', 'Archivo UTF-8 correcto (Chachagüí); el catálogo IDEAM lo escribe «Chachaguí»', V,
  'Descriptiva. No usar como clave.', 'Lectura directa del CSV')
a('year', 'v1 y v2', 'SIVIGILA año', 'Copiado', '2016 y 2022 únicamente; 52 semanas cada uno', V,
  'Solo 2 años: no permite validación temporal.', 'Campo año = año del libro en 100% de filas')
a('epi_week', 'v1 y v2', 'SIVIGILA semana', 'Copiado', '312 claves (municipio, año, semana) únicas; semanas 1–52', V,
  'Verificada para 2016 y 2022. La regla de calendario documentada («primer domingo en o después del 1 de enero») NO generaliza: difiere 7 días de la regla del 4 de enero en 2013, 2014, 2018, 2019 y 2020, y no contempla las 53 semanas de 2014 y 2020.',
  'Calendario recalculado con la regla del 4 de enero; semana 53 observada en SIVIGILA solo en 2014 y 2020')
a('epi_week_start / epi_week_end', 'v1 y v2', 'Calendario INS (derivado)', 'Bloques domingo–sábado anclados a SE52', '0 días de diferencia en las 104 semanas comparadas (4.ª auditoría)', V,
  'Válida para 2016/2022. Para otros años se requiere el calendario INS anual (D-11).', 'Recalculada: SE1 2016 = 2016-01-03; SE1 2022 = 2022-01-02')
a('ira_under5_reported_consultations (v1)', 'v1', 'SIVIGILA iracext_1+2+3', 'Suma de todas las filas del municipio-semana; vacío si no hay fila', 'Reproducido en 312/312 semanas desde los libros originales; 4 semanas sin fila (NA)', U,
  'Nombre y semántica inconsistentes entre documentos: «consultas» (v1), «atenciones» (diccionario), «pacientes» (v2). Es conteo colectivo notificado por las UPGD que reportan, no incidencia. Tasas crudas implícitas de 0.16–0.66 consultas por menor de 5 años y año (p. ej. Chachagüí 2016: 454/1,023) son muy bajas, lo que sugiere que el conteo refleja la cobertura de reporte.',
  'Recalculado: 312/312 coinciden en valor y 312/312 en número de filas')
a('ira_under5_collective_reported_patient_count (v2)', 'v2', 'Ídem v1', 'Renombrado; valores idénticos a v1', 'Idéntico a v1 en las 312 filas', U,
  'El sufijo «patient_count» afirma pacientes; la evidencia local (campos *_exturg, formulario colectivo) apunta a consultas/atenciones. Confirmar con INS antes de fijar el nombre.', 'Comparación v1 vs v2: 0 diferencias de valor')
a('sivigila_source_rows', 'v1 y v2', 'SIVIGILA', 'Conteo de filas fuente del municipio-semana', '0 (4 semanas), 1, 2 o 3 filas', V,
  'Útil como metadato de trazabilidad. No es indicador epidemiológico: refleja el número de UPGD/reportes (Samaniego tiene 3 filas/semana en 2016 y 2 en 2022).', 'Recalculada: 312/312 coinciden')
a('sivigila_duplicate_provider_week_keys (v1) / sivigila_repeated_provider_week_groups (v2)', 'v1 / v2', 'SIVIGILA cod_pre+cod_sub', 'Conteo de grupos repetidos por municipio-semana', '1 grupo (Chachagüí 2016 SE43)', U,
  'La v1 lo llama «duplicado»; la v2 «repetición». Contexto 5.ª auditoría: los grupos repetidos son un patrón de 2012–2018 (827 grupos en Nariño), inexistente en 2019–2022; no es un caso aislado.', 'Reconfirmado: único grupo en los 3 municipios y 2 años')
a('sivigila_week_status', 'v1 y v2', 'SIVIGILA', 'PRESENTE/AUSENTE según haya filas', '308 PRESENTE, 4 AUSENTE', V,
  'AUSENTE = sin fila en la extracción (no es cero). Causa desconocida (D-06).', 'Reconfirmado con el escaneo de los libros (0 filas en Chachagüí SE44 y SE52, Funes SE11 y SE21 de 2016)')
a('temp_min_weekly, temp_min_days_observed, temp_min_coverage_pct', 'v1 y v2', 'IDEAM TSSM_MN_D@{estación}.data', 'Mínimo de los valores diarios de la semana si hay ≥6 de 7 días', '2 NA (Funes 2022 SE5 y SE52, 2 y 5 días); sin flags de calidad IDEAM', U,
  'Recalculada desde los .data: 312/312 valores y 312/312 conteos de días coinciden. Calidad por observación no demostrada. Regla 6/7 propia del piloto.', 'Recalculado desde los archivos diarios')
a('temp_max_weekly, temp_max_days_observed, temp_max_coverage_pct', 'v1 y v2', 'IDEAM TSSM_MX_D@{estación}.data', 'Máximo semanal si ≥6/7 días', '2 NA (mismas semanas)', U,
  'Ídem. Para las 3 estaciones del piloto no hay días con mínima > máxima ni media fuera de [mín, máx].', 'Recalculado: 312/312')
a('temp_mean_weekly, temp_mean_days_observed, temp_mean_coverage_pct', 'v1 y v2', 'IDEAM TSSM_MEDIA_D@{estación}.data', 'Media aritmética de medias diarias si ≥6/7 días', '2 NA (mismas semanas)', U,
  'Promedio de promedios diarios; TSSM_MEDIA_D depende de 3 lecturas diarias (07, 13, 18/19 h) según manual IDEAM.', 'Recalculado: 312/312 (diferencia máxima 1e-14)')
a('population_under5_annual', 'v1 y v2', 'DANE (2 libros municipales)', 'Suma de total edades 0–4, área Total; constante dentro del año', '6/6 municipio-año coinciden con el DANE (1,023/1,089; 373/389; 1,805/1,717)', U,
  'Proyección anual constante en las 52 semanas. Hay un salto de serie entre los libros 2005–2017 y 2018–2042 (mediana +8.2% de 2017 a 2018 en 64 municipios). Sin ajuste, un modelo ve ese salto como señal.', 'Recalculado desde ambos libros DANE')
a('ideam_station_code, ideam_station_name', 'v1 y v2', 'Catálogo IDEAM', 'Asignación por coincidencia de municipio en el catálogo', 'Códigos 52045020, 52055200, 52055060 activos y convencionales; cobertura diaria 98–100%', U,
  'La estación de «Chachagüí» es el Aeropuerto Antonio Nariño (altitud 1,796 m). Identidad verificada por código; representatividad para el municipio NO evaluada (D-03).', 'Estaciones reevaluadas con cobertura semanal 2012–2022')
a('source_dane', 'v1 y v2', 'Nombre de archivo', 'Texto', 'Nombre de libro, sin hoja, rango ni hash', U, 'Trazabilidad insuficiente para reproducir a nivel de celda.', 'Lectura del CSV')
a('source_ideam_tmin / tmax / tmean', 'v1 y v2', 'Nombre de archivo', 'Texto', 'Nombre de archivo .data, sin hash', U, 'Hash existe en reports/cuarta_auditoria/sha256_fuentes.csv (snapshot, no baseline).', 'Lectura del CSV')
a('source_sivigila_file', 'v1 y v2', 'Nombre de archivo', 'Texto', 'Datos_2016_995.xlsx / Datos_2022_995.xlsx, sin hoja ni fila', U, 'Las filas fuente (Excel) solo se documentan en filas_repeticion_sivigila.csv para 2 filas.', 'Lectura del CSV')
a('quality_notes', 'v1 y v2', 'Reglas del piloto', 'Códigos concatenados con «;»', 'En v1: 305 solo IDEAM_SIN_BANDERAS; 4 SIN_FILA...; 2 COBERTURA_METEO...; 1 DUPLICADO...', U,
  'Campo de texto libre, no normalizado. v1 y v2 difieren en 1 celda (SE43 Chachagüí: «DUPLICADO_PROVEEDOR_SEMANA_NO_DEDUPLICADO» frente a «REPETICION_PROVEEDOR_SEMANA_REVISAR_CONSOLIDACION»).', 'Comparación v1 vs v2')
a('sivigila_consolidation_status', 'v2', 'Reglas del piloto', 'SIN_REPETICION_DETECTADA / REPETICION_NO_RESUELTA', '311 / 1', V, 'Solo describe el estado; no consolida.', 'Lectura del CSV')
a('(ausente) precipitación', 'ninguna', 'IDEAM PTPM_CON_INTER', 'No incluida', 'Excluida por equivalencia/unidad no confirmada', P,
  'El piloto no contiene precipitación aunque 53 estaciones superan 80% de semanas con ≥6/7 días.', 'ideam_weekly (5.ª auditoría)')
a('(ausente) humedad / HR_CAL_MEDIA_D', 'ninguna', 'IDEAM', 'No incluida', 'Etiqueta/unidad no confirmadas', P, 'Sin glosario IDEAM.', 'reports/metadatos_variables_ideam.csv')
a('(ausente) denominador de consultas totcext_*', 'ninguna', 'SIVIGILA totcext_1..3', 'No incluida', 'Disponible en los libros', P,
  'Permitiría ajustar por volumen de reporte; no está en ninguna versión del piloto.', 'Escaneo 5.ª auditoría')
a('(ausente) etiqueta de sintético vs real', 'ninguna', '—', '—', 'No aplica al piloto', V,
  'El piloto es 100% real-derivado. backend/data/simulated/ira_cases.csv sí es sintético (data_source) y no debe mezclarse.', 'Lectura del CSV sintético')
pd.DataFrame(pil).to_csv(OUT + 'EVALUACION_DATASET_PILOTO.csv', index=False, encoding='utf-8-sig')
print(len(pil), 'filas piloto')

M = []


def m(rel, crit, ev, evid):
    M.append(dict(relacion=rel, criterio=crit, evaluacion=ev, evidencia=evid))


# ---------------- SIVIGILA + IDEAM
r = 'SIVIGILA + IDEAM'
m(r, 'Identificador territorial', 'SIVIGILA usa DIVIPOLA (cod_mun) del municipio notificador; IDEAM usa código de estación (8 dígitos) y el catálogo trae el municipio solo como texto. No hay clave directa: se requiere una tabla estación→DIVIPOLA. Con coincidencia de nombre normalizado (3 excepciones manuales: Tumaco, El Tablón de Gómez, Santacruz) las 99 estaciones candidatas se asignan a 44 municipios.', 'Cruce 5.ª auditoría entre estaciones_candidatas_ideam.csv y nombres DANE')
m(r, 'Identificador temporal', 'SIVIGILA: año + semana epidemiológica (domingo–sábado). IDEAM: fecha diaria con sello 07:00:00. El puente es un calendario epidemiológico anual que debe construirse y validarse por año.', 'Archivos *.data (Fecha|Valor)')
m(r, 'Cobertura temporal común', '2012–2022 en ambos (574 semanas epidemiológicas con 53 semanas en 2014 y 2020). Los .data de IDEAM llegan hasta 2026.', 'Escaneo SIVIGILA y archivos IDEAM')
m(r, 'Cobertura geográfica', 'SIVIGILA: 64 municipios. Con estación de temperatura con ≥80% de semanas con ≥6/7 días: 12 municipios (Pasto, Aldana, Chachagüí, Funes, Puerres, Pupiales, Samaniego, San Bernardo, Taminango, Tumaco, Túquerres, Tangua). Con estación de precipitación ≥80%: 38 municipios. Sin ninguna estación candidata: 20 municipios.', 'EVALUACION_ESTACIONES_IDEAM.csv; joint_counts (5.ª auditoría)')
m(r, 'Granularidad', 'SIVIGILA semanal por municipio; IDEAM diaria por estación. Se debe agregar IDEAM a semana (sin interpolar).', 'Ver sección de agregación en INFORME_GENERAL.md')
m(r, 'Variables compatibles', 'Temperatura mínima, máxima y media (TSSM_MN_D, TSSM_MX_D, TSSM_MEDIA_D) con significado documentado en el manual IDEAM GDI-M005. Precipitación PTPM_CON_INTER: sufijo no confirmado. Humedad, punto de rocío y tensión de vapor: no confirmadas.', 'reports/metadatos_variables_ideam.csv')
m(r, 'Limitaciones', 'Estación puntual ≠ municipio (las estaciones con temperatura van de 1 m a 3,141 m de altitud). Estación asignada por nombre de municipio, no por distancia/altitud. Sin flags de calidad. Estación de Aldana con TSSM_MN_D idéntica a TSSM_MX_D en 4,016/4,016 días (no usable). 52 municipios sin estación de temperatura ≥80%.', 'EVALUACION_ESTACIONES_IDEAM.csv')
m(r, 'Viabilidad', 'Viable con restricciones (12 municipios en temperatura; 38 en precipitación si se confirma la etiqueta)', 'Resumen')
# ---------------- SIVIGILA + DANE
r = 'SIVIGILA + DANE'
m(r, 'Identificador territorial', 'Ambos usan DIVIPOLA de 5 dígitos: los 64 municipios coinciden. Excepciones en SIVIGILA: 1 fila 2012 con código 52000 y 9 filas con código 52xxx pero departamento notificador distinto.', 'Escaneo SIVIGILA (nmun_notif/ndep_notif) vs DANE MPIO')
m(r, 'Identificador temporal', 'DANE: año calendario (proyección a mitad de año). SIVIGILA: año/semana epidemiológica. El año epidemiológico no coincide exactamente con el año calendario (p. ej. SE1 2018 empieza el 31/12/2017).', 'Calendario recalculado')
m(r, 'Cobertura temporal común', '2012–2022 completa: 704/704 municipio-año con área Total (2012–2017 del libro 2005–2017; 2018–2022 del libro 2018–2042).', 'Escaneo DANE 5.ª auditoría')
m(r, 'Cobertura geográfica', '64/64 municipios de Nariño.', 'Escaneo DANE')
m(r, 'Granularidad', 'Anual (DANE) vs semanal (SIVIGILA). La población anual se asigna constante a las semanas del año; no es estimación semanal.', '—')
m(r, 'Variables compatibles', 'Población 0–4 años (suma de edades simples 0,1,2,3,4; total = hombres+mujeres en 100% de las filas) frente a IRA consulta externa/urgencias <1, 1 y 2–4 años.', 'Escaneo DANE')
m(r, 'Limitaciones', 'El numerador es un conteo de consultas notificadas por UPGD reportantes; el denominador es población del municipio (no de residencia de los atendidos; incluye cobertura de aseguramiento, migración y atención en otro municipio). Salto de serie 2017→2018 (mediana +8.2%; 53 de 64 municipios >+5%). 13 municipios con <500 menores de 5 años en 2022 (tasas inestables).', 'dane_a/dane_b (5.ª auditoría)')
m(r, 'Viabilidad', 'Viable con restricciones (denominador anual utilizable; tasa cruda no es incidencia)', 'Resumen')
# ---------------- IDEAM + DANE
r = 'IDEAM + DANE'
m(r, 'Identificador territorial', 'Sin clave común directa: solo comparten el municipio (texto en IDEAM, DIVIPOLA en DANE) a través de la tabla estación→municipio.', 'Cruce 5.ª auditoría')
m(r, 'Identificador temporal', 'Diario (IDEAM) vs anual (DANE).', '—')
m(r, 'Cobertura temporal común', '2012–2022.', '—')
m(r, 'Cobertura geográfica', 'La que haya estación asignada (44 municipios con alguna estación; 12 con temperatura útil).', 'EVALUACION_ESTACIONES_IDEAM.csv')
m(r, 'Granularidad', 'Diaria vs anual; no se relacionan directamente.', '—')
m(r, 'Variables compatibles', 'Ninguna relación analítica propia; la población solo serviría para describir el municipio al que se asigna una estación o ponderar.', '—')
m(r, 'Limitaciones', 'La relación es indirecta y solo existe a través de SIVIGILA.', '—')
m(r, 'Viabilidad', 'No viable como relación independiente (solo indirecta)', 'Resumen')
# ---------------- Triple
r = 'SIVIGILA + IDEAM + DANE'
m(r, 'Identificador territorial', 'DIVIPOLA como columna vertebral; estación como atributo asignado al municipio.', '—')
m(r, 'Identificador temporal', 'Semana epidemiológica como unidad; DANE anual por año epidemiológico/calendario (a decidir); IDEAM agregado por semana.', '—')
m(r, 'Cobertura temporal común', '2012–2022 (2020–2021 con quiebre estructural del conteo IRA).', 'Escaneo SIVIGILA')
m(r, 'Cobertura geográfica', '12 municipios con temperatura (6,282 municipio-semanas con IRA completa y temperatura mín/máx/media ≥6/7 días); 38 con precipitación (19,934 municipio-semanas, sujeto a confirmar etiqueta). Con temperatura Y precipitación: 12 municipios, 6,273 municipio-semanas.', 'joint_counts (5.ª auditoría)')
m(r, 'Granularidad', 'Semanal por municipio.', '—')
m(r, 'Variables compatibles', 'IRA (iracext_1..3); temperatura (3 variables); población 0–4 (denominador); opcionalmente totcext_1..3 (denominador de consultas).', '—')
m(r, 'Limitaciones', 'Todas las anteriores. Piloto actual: 3 municipios y 2 años (312 municipio-semanas).', 'EVALUACION_DATASET_PILOTO.csv')
m(r, 'Viabilidad', 'Viable con restricciones, para un subconjunto de municipios; no para los 64', 'Resumen')
pd.DataFrame(M).to_csv(OUT + 'MATRIZ_COMPATIBILIDAD_FUENTES.csv', index=False, encoding='utf-8-sig')
print(len(M), 'filas matriz')
