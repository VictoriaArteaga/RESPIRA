# Auditoría local SIVIGILA 995, 2012–2022

**Fecha de corte:** 26 de octubre de 2026. **Alcance:** lectura de los 11 libros locales `Datos_{año}_995.xlsx`; ningún libro fuente fue modificado. Los resultados aquí son de auditoría de estructura y calidad, no de validación epidemiológica.

## Hallazgo principal

El evento 995 corresponde a **morbilidad por IRA con notificación colectiva semanal**. La unidad contenida en estos archivos son conteos agregados por grupos de edad, servicio y UPGD, no una fila por paciente. El protocolo INS indica notificación colectiva semanal obligatoria por las UPGD y uso de RIPS como numeradores/denominadores. Por ello el piloto usa un conteo concreto de atenciones de consulta externa/urgencias en 0–4 años (`IRACEXT_1 + IRACEXT_2 + IRACEXT_3`) y no lo denomina personas, casos únicos ni incidencia.

Fuentes oficiales: [Protocolo INS IRA 2024](https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_IRA%202024.pdf), [formulario colectivo INS 995](https://www.ins.gov.co/buscador-eventos/Lineamientos/995_IRA_Colectiva_2024.pdf), [estructura de registros SIVIGILA 2016](https://www.ins.gov.co/Direcciones/Vigilancia/sivigila/Documents/Anexo%202%20Estructura%20de%20los%20registros%20de%20notificaci%C3%B3n.pdf) y [diccionario de datos básicos](https://www.ins.gov.co/BibliotecaDigital/diccionario-datos-basicos-sivigila.pdf).

## Inventario anual

| Año | Hoja detallada usada | Filas aprox. (incluye encabezado/títulos) | Columnas | Observación de estructura |
|---:|---|---:|---:|---|
| 2012 | `995 52` | 144,299 | 77 | Otra hoja `Base Recibida` con dimensión igual; se usa una sola vista detallada para evitar contar dos presentaciones del mismo libro. |
| 2013 | `Hoja1` | 187,955 | 84 | Esquema de 84 campos. |
| 2014 | `Hoja1` | 178,567 | 84 | Esquema de 84 campos. |
| 2015 | `Hoja1` | 184,986 | 84 | Esquema de 84 campos. |
| 2016 | `Hoja1` | 231,882 | 84 | Esquema de 84 campos. |
| 2017 | `EVENTO 995` | 238,173 | 84 | Etiquetas de evento deben verificarse junto al código. |
| 2018 | `Hoja1` | 240,895 | 84 | Esquema de 84 campos. |
| 2019 | `Final` | 245,200 | 85 | `Hoja1` es una vista resumida/pivote de 55,113×10; no se suma junto con la hoja detallada. |
| 2020 | `995_2020_Depurada` | 215,730 | 84 | Esquema de 84 campos. “Depurada” es parte del nombre de la hoja, no prueba de criterios de depuración trazables. |
| 2021 | `ACUMULADO` | 1,048,576 | 85 | Alcanza el límite de filas de Excel; posible truncamiento que requiere contraste con entrega oficial. No se usa en piloto. |
| 2022 | `995` | 235,740 | 83 | Un campo menos que el esquema frecuente; revisar cambios de versión antes de empalmes multianuales. |

Las dimensiones son las observadas de hoja e incluyen filas de encabezado/título, por tanto no deben interpretarse directamente como número de registros. En el barrido dirigido de los años piloto, todos los renglones de datos observados tenían `cod_eve=995`: 231,881 en 2016 y 235,738 en 2022. Los otros años conservan su revisión estructural; este trabajo no recalculó estadísticos de contenido completos de cada libro.

## Semántica y reglas de lectura

- `cod_mun` se interpreta como código DIVIPOLA del municipio notificador; `nmun_notif` y `ndep_notif` sirven como controles. No representa residencia. El portal de estadísticas rutinarias INS describe sus publicaciones agregadas según ocurrencia/procedencia; esa publicación no cambia la semántica de las filas locales del formulario colectivo que se usaron aquí. En consecuencia, el piloto habla de municipio de notificación.
- `año` y `semana` suministrados en el formulario son la clave temporal epidemiológica. `fec_not` significa fecha de notificación; no es fecha de ocurrencia ni se usa para reasignar la semana.
- `cod_pre` y `cod_sub` identifican prestador/subíndice para el control de repetición por proveedor-semana; `num_con` es consecutivo, no ID de persona. No se deduplican automáticamente renglones.
- La estructura oficial INS 2016 relaciona `IRACEXT_1`, `_2`, `_3` con <1, 1 y 2–4 años. Su suma es el indicador de atenciones reportadas de 0–4 años de consulta externa/urgencias. El formulario y nombres de campo variaron por versión; esta selección se debe confirmar contra el diccionario de cada año antes de ampliar a toda la serie.
- Semanas del piloto se conservan según formulario. El calendario de semana usado para clima es domingo–sábado, con primera semana iniciando el primer domingo en o después del 1 de enero; para 2016 y 2022 hay 52 semanas, terminando el 31 de diciembre. Ver la [metodología INS de estadísticas rutinarias](https://www.ins.gov.co/Direcciones/Vigilancia/Paginas/SIVIGILA.aspx) y la ficha metodológica de vigilancia INS. El calendario no se usa para corregir valores de semana SIVIGILA.

## Calidad y riesgos

- Se observaron cambios de disposición, hoja detallada, y número de columnas; una estructura común no se debe asumir entre años sin mapeo por encabezado.
- Los códigos pueden venir como texto o número y con formatos distintos; normalizar a DIVIPOLA de cinco caracteres y conservar el valor original en un proceso de integración completo.
- En 2012 hay dos hojas de dimensiones iguales; en 2019 conviven hoja resumida y detallada. No sumar vistas alternativas.
- En 2021 la hoja llega exactamente a 1,048,576 filas, máximo de XLSX. El truncamiento es sospecha técnica, no hecho demostrado; contrastar con fuente oficial antes de usar ese año.
- Los libros contienen columnas potencialmente identificables/contacto. Ninguna se exportó al piloto; se limita a agregados municipio-semana.
- La indicación del protocolo de validar registros repetidos no autoriza a borrar filas en esta auditoría. Los duplicados se cuentan, se informan y se conservan en suma exploratoria para que su impacto pueda revisarse.

## Control cuantitativo de los años del piloto

| Año | Registros en el libro (sin encabezado) | Nariño | Chachagüí | Funes | Samaniego | Duplicados prestador-semana en selección | Semanas notificadas faltantes |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2016 | 231,881 | 8,026 | 51 filas / 50 semanas | 50 filas / 50 semanas | 156 filas / 52 semanas | 1 clave repetida, en Chachagüí, semana 43; se conservaron ambas filas | Chachagüí 44, 52; Funes 11, 21 |
| 2022 | 235,738 | 7,191 | 53 filas / 52 semanas | 52 filas / 52 semanas | 105 filas / 52 semanas | 0 | Ninguna |

En 2016 la clave repetida fue Chachagüí, semana 43, proveedor `5224001399`, subíndice `01`; los consecutivos 263 y 264 contienen valores distintos de las partes IRACEXT, así que no son filas idénticas. Se conserva la suma por semana y se marca como no deduplicada. Las semanas sin fila se dejan vacías en el piloto, nunca se convierten a cero.

## Diccionario mínimo del piloto

El archivo [diccionario_sivigila_995.csv](diccionario_sivigila_995.csv) documenta los campos relevantes, unidad, reglas y cautelas. Las fuentes y códigos desconocidos se mantienen pendientes en vez de inferir significado de la posición de columna.
