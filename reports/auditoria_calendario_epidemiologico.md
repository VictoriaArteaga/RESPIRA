# Auditoría del calendario epidemiológico del piloto

**Estado:** calendario de 2016 y 2022 consistente con evidencia oficial consultada para esas dos anualidades. No se usó calendario ISO ni se reasignó SIVIGILA a partir de `fec_not`.

## Fuentes y evidencia

No se encontró un calendario tabular anual local en el proyecto. La documentación de procedimiento del INS define la semana epidemiológica como domingo a sábado. Los boletines INS de cierre de 2016 y de 2022 identifican expresamente SE 52 como **25–31 de diciembre**. Con ese ancla oficial, y la definición domingo–sábado en semanas consecutivas, las 52 ventanas se enumeran hacia atrás desde SE 52 y no requieren inferirlas desde calendario ISO. Fuentes: [boletín INS, SE 52 de 2016](https://www.ins.gov.co/buscador-eventos/BoletinEpidemiologico/2016%20Bolet%C3%ADn%20epidemiol%C3%B3gico%20semana%2052%20-.pdf), [boletín INS, SE 52 de 2022](https://www.ins.gov.co/BibliotecaDigital/2022-boletin-epidemiologico-semana-52.pdf), y [ficha metodológica INS de vigilancia](https://www.ins.gov.co/BibliotecaDigital/8-ficha-metodologia-de-la-operacion-estadistica-de-vigilancia-de-eventos-de-salud-publica.pdf) (la URL está listada por INS, aunque la consulta directa devolvió 404; la definición se encontró indexada en la propia búsqueda INS). La estructura INS de registros colectivos indica que `SEMANA` se refiere al calendario vigente, rango 1–53, y `AÑO` es el año correspondiente a la semana epidemiológica.

## Comparación con el piloto actual

| Año | Semana | Inicio según ancla oficial | Fin según ancla oficial | Inicio piloto actual | Fin piloto actual | Diferencia |
|---:|---:|---|---|---|---|---|
| 2016 | 1 | 2016-01-03 | 2016-01-09 | 2016-01-03 | 2016-01-09 | 0 días |
| 2016 | 52 | 2016-12-25 | 2016-12-31 | 2016-12-25 | 2016-12-31 | 0 días |
| 2022 | 1 | 2022-01-02 | 2022-01-08 | 2022-01-02 | 2022-01-08 | 0 días |
| 2022 | 52 | 2022-12-25 | 2022-12-31 | 2022-12-25 | 2022-12-31 | 0 días |

Las fechas SE52 (25–31 de diciembre) son explícitas en cada boletín. Las fechas SE1 y las intermedias se derivan hacia atrás/adelante desde esa ancla, conforme a la regla INS domingo–sábado; no aparecen impresas como una tabla anual completa en los documentos consultados. La comparación de **las 104 semanas** está en [`reports/cuarta_auditoria/calendario_semana_epi.csv`](cuarta_auditoria/calendario_semana_epi.csv), con columnas `derived_INS_calendar_start/end` que hacen visible esta derivación. Las semanas intermedias son bloques consecutivos de siete días anclados a SE52.

## Días de borde

En 2016, 1–2 de enero fueron viernes y sábado; forman la parte final de la semana domingo 2015-12-27 a sábado 2016-01-02, por lo que pertenecen al año/SE52 epidemiológico anterior. En 2022, 2022-01-01 fue sábado, parte de SE52 que inició 2021-12-26. No son días sin semana: quedan fuera de la selección por **año epidemiológico 2016/2022** porque pertenecen a la SE52 del año anterior. La primera semana del año epidemiológico sí empieza 3 de enero de 2016 y 2 de enero de 2022.

Para SIVIGILA se preservan literalmente `año` y `semana`; no se fabrican fechas por notificación. Las fechas se asignan solo a las fechas diarias IDEAM para agregar temperatura a una semana comparable. El piloto actual coincide en las fechas de límites y en las 52 semanas con la secuencia oficial documentada; no requiere reconstrucción, pero su script de auditoría conserva la comprobación para detectar cambios.

## Límite

La evidencia consultada no es un archivo INS descargado que liste todas las 52 filas de cada año ni demuestra qué programa generó la extracción local. La regla es sólida para el rango de estas dos anualidades por la combinación de definición domingo–sábado y fechas oficiales de SE52, y concuerda con la estructura/campos de los libros. Para ampliar a años que puedan tener SE53, solicitar o preservar el calendario INS específico del año y no extrapolar la regla de 52 semanas.
