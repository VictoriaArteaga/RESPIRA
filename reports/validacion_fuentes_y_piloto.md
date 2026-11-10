# Validación final de fuentes y construcción del piloto RESPIRA

**Fecha:** 26 de octubre de 2026. **Decisión:** **B — listo para piloto exploratorio, no para integración completa**.

## Qué se entrega

- [Estaciones candidatas IDEAM](estaciones_candidatas_ideam.csv): 99 códigos de estación con metadatos, cobertura 2012–2022, huecos máximos, cruce por código del catálogo y justificación. Son candidatas, no estaciones certificadas.
- [Metadatos IDEAM](metadatos_variables_ideam.csv): semántica/unidad, evidencia oficial, estado de confirmación y decisión de uso para ocho etiquetas.
- [Auditoría SIVIGILA 995 2012–2022](auditoria_sivigila_995_2012_2022.md) y [diccionario mínimo](diccionario_sivigila_995.csv).
- [Piloto semanal 2016 y 2022](../data/processed/pilot/piloto_respira_2016_2022.csv): 312 filas, tres municipios × dos años × 52 semanas. No contiene nombres personales, contactos, NIT ni identificadores de prestador.
- [Segunda auditoría preservada](../docs/data-audit/segunda-auditoria/README.md), con informe, resúmenes y SHA256 locales.

## Diseño del piloto y reglas reproducibles

Se eligieron **Chachagüí (52240), Funes (52287) y Samaniego (52678)**, con estaciones asignadas por coincidencia exacta entre código de estación y municipio en el catálogo IDEAM: `52045020`, `52055200` y `52055060`. Las tres estaciones seleccionadas figuran activas y convencionales. La selección usa cobertura de temperatura en ambos años y no proximidad geográfica. Pasto/Obonuco (`52045010`) no fue seleccionado porque no tiene cobertura térmica en 2016 y presenta huecos largos.

Los años **2016 y 2022** permiten comprobar el empalme de los dos libros de población DANE (2005–2017 y 2018–2042). La población 0–4 se obtiene de área `Total`, sumando edades simples 0, 1, 2, 3 y 4 en los campos de población total. Los seis municipio-año tienen valor: Chachagüí 1.023/1.089; Funes 373/389; Samaniego 1.805/1.717 (2016/2022).

La fecha de cada semana climática es domingo–sábado, con semana 1 empezando el primer domingo en o después del 1 de enero; cada año piloto tiene 52 semanas. Mínima semanal = mínimo de valores diarios `TSSM_MN_D`; máxima semanal = máximo de `TSSM_MX_D`; media semanal = media aritmética de `TSSM_MEDIA_D`. Se emite valor semanal solo con **al menos 6 de 7 días** válidos por variable; los días observados y cobertura porcentual se guardan en cada fila. Esta es una regla explícita del piloto, no una norma de IDEAM.

La métrica SIVIGILA es `IRACEXT_1 + IRACEXT_2 + IRACEXT_3`, conteo colectivo notificado de atenciones IRA externas/urgencias en grupos <1, 1 y 2–4 años. Se agrupa por `cod_mun`, `año`, `semana` reportados y no desde `fec_not`. No equivale a personas únicas, casos de residentes ni incidencia. Si una semana no tiene filas, el conteo queda vacío, nunca cero. Duplicados proveedor-semana se conservan, y se marca el estado de calidad.

La precipitación no se incorpora: el archivo usa `PTPM_CON_INTER` y la fuente oficial consultada documenta `PTPM_CON`, pero no acredita su equivalencia exacta. `HR_CAL_MEDIA_D`, `TPR_CAL` y `TV_CAL` tampoco se usan por semántica/unidad no confirmada para sus etiquetas exactas. El IDEAM describe cómo calcula los derivados térmicos, pero los archivos locales carecen de banderas que demuestren aprobación/validación por observación.

## Validaciones ejecutadas

- **Esquema/llave:** 312 filas, 312 claves únicas `(municipality_divipola, year, epi_week)`, todos los años con 52 semanas y códigos municipales de cinco dígitos.
- **Fuentes y población:** 6 de 6 municipio-año con población; se conserva libro DANE de origen en cada fila.
- **Cobertura SIVIGILA:** 308 semanas con filas y 4 sin fila (Chachagüí 2016 semanas 44 y 52; Funes 2016 semanas 11 y 21). 2016 tiene una clave repetida proveedor-semana en Chachagüí, semana 43, con valores distintos; ambas filas se conservaron en el agregado y se registró la alerta. 2022 no tiene semana ausente ni clave repetida en estos municipios.
- **Cobertura IDEAM:** 2 semanas por variable sin alcanzar el umbral de 6 días; quedan como `NA`, con cobertura guardada. No se aplicó corrección de extremos ni imputación.
- **Privacidad y alcance:** el CSV piloto no incluye columnas personales ni códigos de UPGD. No se cambió ningún archivo crudo. Ninguna tasa o asociación causal se calcula.
- **Límite del universo auditado:** 2021 llega al máximo de filas de XLSX; su integridad aún no está probada, por eso no se seleccionó. La auditoría de SIVIGILA documenta estructura anual, pero el análisis de contenido detallado se enfocó en 2016 y 2022.

## Decisión y pendientes antes de integración

**B — listo para piloto exploratorio; no listo para integración completa.** Se dispone de un dataset pequeño, reproducible y con faltantes visibles para revisar reglas y controles. Antes de una integración multianual o uso inferencial hacen falta: confirmación escrita IDEAM de `PTPM_CON_INTER` y de etiquetas/unidades pendientes; banderas de calidad y estado preliminar/definitivo de las series; verificación del calendario epidemiológico oficial aplicado en cada archivo anual; conciliación de duplicados y semanas notificadas ausentes; confirmación de completitud del archivo 2021; y mapeo versionado de encabezados/colectivos SIVIGILA por año. El conteo colectivo tampoco puede interpretarse como incidencia individual.

## Referencias primarias

- INS, [Protocolo de vigilancia de infección respiratoria aguda, 2024](https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_IRA%202024.pdf).
- INS, [formulario de notificación colectiva evento 995](https://www.ins.gov.co/buscador-eventos/Lineamientos/995_IRA_Colectiva_2024.pdf).
- INS, [estructura de los registros de notificación SIVIGILA](https://www.ins.gov.co/Direcciones/Vigilancia/sivigila/Documents/Anexo%202%20Estructura%20de%20los%20registros%20de%20notificaci%C3%B3n.pdf) y [diccionario de datos básicos](https://www.ins.gov.co/BibliotecaDigital/diccionario-datos-basicos-sivigila.pdf).
- IDEAM, [Manual de control de calidad y verificación GDI-M005 v2](https://ideam.gov.co/sites/default/files/mapa-de-procesos/gdi-m005_manual_control_de_calidad_verificacion_v2.pdf).
- IDEAM, [respuesta a radicado 20259050026354_SM (2025)](https://www.ideam.gov.co/sites/default/files/transparencia/planeacion/respuesta_radicado_no_20259050026354_sm.pdf).
- DANE, [proyecciones de población](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion).
- INS, [portal SIVIGILA](https://www.ins.gov.co/Direcciones/Vigilancia/Paginas/SIVIGILA.aspx). La regla de calendario semanal usada arriba es la regla operativa del piloto y debe cotejarse con la ficha metodológica anual si se expande.
