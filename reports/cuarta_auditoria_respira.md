# Cuarta auditoría y validación del piloto RESPIRA

**Fecha:** 26 de octubre de 2026. **Decisión:** **B — apto para análisis exploratorio con limitaciones.** Esta auditoría valida consistencia reproducible de la transformación piloto; no establece por sí sola validez científica, representatividad municipal ni aptitud para entrenar una IA.

## Objetivo y alcance

Resolver con evidencia local/oficial las alertas del piloto 2016/2022 de Chachagüí, Funes y Samaniego. No se entrenó modelo, no se generó predicción, no se conectó la aplicación o base de datos. Se leyeron archivos originales; se escribieron resultados derivados únicamente en los directorios de auditoría.

## Archivos revisados

- Piloto `data/processed/pilot/piloto_respira_2016_2022.csv` y salidas de la segunda auditoría preservada en `docs/data-audit/segunda-auditoria/`.
- Auditoría IDEAM/DANE de la segunda etapa en `data/reports/auditoria_segunda_fuentes.md` y el informe técnico anterior `data/reports/INFORME_AUDITORIA_DATASETS_RESPIRA_20261025.md` (el informe de la tercera etapa estaba en `data/reports`, no en `reports`).
- `reports/estaciones_candidatas_ideam.csv`, `reports/metadatos_variables_ideam.csv`, `reports/auditoria_sivigila_995_2012_2022.md`, `reports/diccionario_sivigila_995.csv`.
- SIVIGILA 2016 y 2022 para una recalculación focalizada del piloto; SIVIGILA 2021 para inspección estructural sin leer/exportar datos sensibles; DANE municipal 2005–2017 y 2018–2042; catálogo IDEAM y 18 series diarias térmicas de las tres estaciones/años seleccionados.
- Inventario de hashes en `reports/cuarta_auditoria/sha256_fuentes.csv`. Los tres SHA-256 escritos previamente para artefactos de segunda auditoría coinciden. No había hashes de adquisición anteriores para los XLSX, `.data` ni para el primer CSV piloto: los hashes incluidos para estos son snapshots de esta revisión, no comparación retrospectiva de inmutabilidad.

## Metodología y resultados

### Calendario epidemiológico

No hay tabla anual de calendario local en los documentos de auditoría disponibles. La documentación de vigilancia INS define semana epidemiológica domingo–sábado; sus boletines oficiales fijan SE52 de 2016 y SE52 de 2022 entre el 25 y 31 de diciembre. Al enumerar 52 bloques semanales consecutivos desde ese ancla, las ventanas 2016-01-03–2016-01-09 y 2022-01-02–2022-01-08 de SE1 del piloto coinciden con el calendario oficial. La comparación de las 104 semanas está en `reports/cuarta_auditoria/calendario_semana_epi.csv`; no se usó semana ISO. Los días 1–2 de enero de 2016 y 1 de enero de 2022 corresponden a la SE52 del año epidemiológico anterior, no a fechas sin semana.

Fuentes: [INS, definición domingo–sábado](https://www.ins.gov.co/BibliotecaDigital/8-ficha-metodologia-de-la-operacion-estadistica-de-vigilancia-de-eventos-de-salud-publica.pdf), [BES INS semana 52 de 2016](https://www.ins.gov.co/buscador-eventos/BoletinEpidemiologico/2016%20Bolet%C3%ADn%20epidemiol%C3%B3gico%20semana%2052%20-.pdf), [BES INS semana 52 de 2022](https://www.ins.gov.co/BibliotecaDigital/2022-boletin-epidemiologico-semana-52.pdf). La ficha metodológica INS aparece indexada con esta definición; su URL consultada directamente devolvió 404, por lo que los dos boletines son la evidencia anual más fuerte. El diccionario de registros admite rango de semana 1–53: años adicionales requieren calendario anual específico.

### Repetición SIVIGILA en Chachagüí, 2016, SE43

El agrupamiento por municipio-año-semana-UPGD-sede detecta dos filas fuente, Excel 204616 y 207474. Sus `NUM_CON` son 263 y 264; `IRACEXT_1/2/3` son 4/0/4 y 0/0/1, respectivamente. No son filas idénticas. La estructura INS dice que `NUM_CON` es consecutivo por cada reporte de la misma UPGD en una misma semana y evento; por tanto, coincidir en proveedor-semana no hace de ellas duplicados. No existe evidencia que resuelva si el reporte posterior acumula una corrección, reemplaza al primero o es aditivo. Se conservan las dos filas y su suma exploratoria 9, con estado `REPETICION_NO_RESUELTA`; no se elimina ni se afirma doble conteo probado. Evidencia minimizada: `reports/cuarta_auditoria/filas_repeticion_sivigila.csv`. Ver [estructura colectiva INS 2016](https://www.ins.gov.co/Direcciones/Vigilancia/sivigila/Documents/Anexo%202%20Estructura%20de%20los%20registros%20de%20notificaci%C3%B3n.pdf).

### Semántica de IRA y comparabilidad

La estructura INS 2016 para evento colectivo 995 define `IRACEXT_1` como total IRA de consulta externa <1 año, `_2` de 1 año y `_3` de 2–4 años; cada campo es el número reportado de pacientes del grupo en la ficha. La suma operativa es entonces un **conteo colectivo semanal de pacientes reportados en consulta externa con IRA, grupos 0–4**, no personas únicas entre reportes/semanas ni incidencia/prevalencia. El protocolo 2024 confirma que evento 995 es notificación colectiva semanal; no convierte sus celdas en una línea por paciente. En los libros locales 2016 y 2022 están presentes los tres nombres exactos y el escaneo dirigido de sus filas recalcula los valores del piloto; los libros difieren en número de columnas (84/83 y otros cambios de disposición), por lo que la equivalencia multianual queda limitada a estos campos y años, no validada automáticamente para toda la serie. Falta diccionario/versionado específico de la extracción local 2022 y regla para sucesivos reportes por UPGD.

Fuentes: [estructura INS 2016, evento 995](https://www.ins.gov.co/Direcciones/Vigilancia/sivigila/Documents/Anexo%202%20Estructura%20de%20los%20registros%20de%20notificaci%C3%B3n.pdf), [protocolo IRA INS 2024](https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_IRA%202024.pdf), [formulario colectivo INS 995](https://www.ins.gov.co/buscador-eventos/Lineamientos/995_IRA_Colectiva_2024.pdf).

### Integridad SIVIGILA 2021

Hay una versión local, `Datos_2021_995.xlsx`, hoja `ACUMULADO`, 1.048.576 filas × 85 columnas y 77.043.344 bytes; alcanza el máximo de filas de Excel. No se encontraron archivos alternos/fragmentos autorizados locales ni conteo de extracción, hash oficial o manifiesto de origen. **Integridad no demostrada; 2021 no validado y excluido de integración que requiera completitud.** Llegar al límite no prueba por sí solo truncamiento, pero tampoco permite afirmar integridad por solo abrir el libro. Detalle en `reports/auditoria_integridad_sivigila_2021.md`.

### Faltantes de notificación

El recálculo contra fuentes encuentra que Chachagüí no tiene filas para 2016 SE44/52 y Funes no tiene filas para SE11/21; ambos municipios sí tienen registros en otras semanas del año. Una ausencia de fila en esta extracción no permite distinguir no-notificación, dato no entregado o notificación real de cero. Las cuatro celdas siguen vacías (no cero) y limitan análisis de continuidad; solicitar validación a INS/entidad territorial. En 2022 los tres municipios tienen registros en las 52 semanas.

### Agregación IDEAM

Los códigos `52045020`, `52055200` y `52055060` concuerdan por código con Chachagüí, Funes y Samaniego en el catálogo utilizado; para Chachagüí el catálogo presenta una variante ortográfica sin diéresis (`Chachaguí`), normalizada al cruzar código y municipio. Los metadatos muestran Nariño, estaciones convencionales y estado activo. Esto verifica identidad catalogal, no representatividad climática de todo el municipio. El script reagrupa fechas diarias usando el calendario INS validado: mínimo de TSSM_MN_D, máximo de TSSM_MX_D y promedio aritmético de TSSM_MEDIA_D cuando hay al menos 6/7 días por semana. Los días, coberturas y semanas bajo umbral se listan en `reports/cuarta_auditoria/cobertura_meteorologica.csv`; no se rellenan faltantes ni se eliminan extremos. En Funes 2022, las tres variables tienen 2/7 días en SE5 y 5/7 en SE52: ambas quedan vacías por regla 6/7. En las 18 series estación-variable-año no se detectaron fechas diarias duplicadas ni filas de datos no parseables; el encabezado `Fecha|Valor` se reconoce como encabezado. Esta regla de 6/7 es del piloto, no estándar IDEAM. Las extracciones no incluyen flags individuales de calidad; el manual describe cálculo de derivados, pero no prueba la aprobación de cada dato.

Se excluyen precipitación `PTPM_CON_INTER`, HR, `TPR_CAL`, `TV_CAL` porque la etiqueta/unidad exacta sigue sin confirmación oficial suficiente. Tampoco se aplica límite numérico de plausibilidad: no se encontró umbral documentado por estación/variable para esta extracción. Se mantienen valores observados y se solicitan banderas/metadatos a IDEAM.

### Población DANE

Los seis registros piloto son constantes en todas las semanas de su municipio-año, tienen código DIVIPOLA de cinco caracteres y citan el libro temporal correcto: 2005–2017 para 2016 y 2018–2042 para 2022. Las poblaciones 0–4 son Chachagüí 1.023/1.089, Funes 373/389 y Samaniego 1.805/1.717 (2016/2022). La segunda auditoría ya recorrió los libros completos: usa área `Total` y suma población total de edades simples 0–4; no suma subáreas ni sexo junto con Total. La validación automática contrasta presencia, estabilidad anual y procedencia del piloto con esa auditoría preservada. Son proyecciones anuales, no medición semanal.

## Validaciones automáticas y artefactos

La rutina `data/scripts/auditar_cuarta_respira.py` ejecutó **53 comprobaciones: 47 PASS, 0 FAIL y 6 WARNING/PENDING**. Revisa existencia/esquema/claves del piloto, calendario, campos/valores SIVIGILA, huecos y agregados, 2021, catálogo y observaciones diarias IDEAM, reglas de agregación, completitud semanal y procedencia DANE. Resultados legibles y CSV están en `reports/cuarta_auditoria/`. La salida separa errores técnicos de warnings/pending; no establece rangos automáticos de descarte.

La versión `reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv` es derivada y versionada: preserva filas y valores, cambia la etiqueta de “duplicado proveedor-semana” a “repetición proveedor-semana” y da al indicador un nombre que expresa conteo colectivo reportado. El piloto previo queda intacto para comparación.

## Hallazgos resueltos, pendientes y decisión

**Resueltos para el piloto:** calendario de 2016/2022 anclado a evidencia anual INS; semanas sin filas confirmadas en la extracción y representadas como faltantes; estaciones verificadas por código exacto; valores meteorológicos semanales recalculables desde archivo diario; población con libro y regla DANE documentados; el supuesto “duplicado” se reclasifica como reporte repetido no resuelto, no fila idéntica.

**Pendientes:** consolidación semántica del reporte sucesivo `NUM_CON`; completitud de 2021; confirmación IDEAM de etiquetas, banderas y representación climática; diccionario anual SIVIGILA completo/versión de 2022; motivo de no-notificación en cuatro semanas; calendario INS anual para años a ampliar y para posibles SE53; rangos oficiales de plausibilidad por observación.

**Estado B — apto para análisis exploratorio con limitaciones.** Las reglas ejecutadas son rastreables para el subconjunto piloto, pero cuatro semanas sin fila, un grupo de reportes cuya relación aditiva no se resolvió, falta de flags IDEAM y año 2021 no validado impiden integración ampliada y conclusiones científicas sobre riesgo o incidencia. No es apto todavía para entrenamiento predictivo.

Decisiones, responsables sugeridos e impactos: `reports/decisiones_pendientes_datos.md`. Instrucciones reproducibles: `docs/data-audit/cuarta-auditoria/README.md`.
