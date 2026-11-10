# Inventario de scripts — quinta auditoría

**Fecha:** 5 de noviembre de 2026. **Autorización:** opción C del usuario (copiar a `data/scripts/` sin modificar).

**Qué es esto.** Copias **sin modificar** de los scripts usados en la quinta auditoría. Se copiaron por preservación y trazabilidad. **No se ejecutaron, no se corrigieron y no se refactorizaron.** Están en la subcarpeta `quinta_auditoria/` para no mezclarlos con los dos scripts anteriores ni colisionar con nombres genéricos; ningún archivo existente fue reemplazado (`cp -n`, 0 conflictos).

## Advertencias de uso

1. Muchos scripts dependen de **archivos intermedios en el directorio de trabajo** (`nar_*.csv`, `*.pkl`, `cols_*.json`) que no se copiaron: fueron resultados temporales de la sesión. Para reproducir hay que regenerarlos en el orden: `scan_siv.py` → `an1.py` → `an2.py`/`an3.py`/`an4.py`; `scan_dane.py` → `an5.py`; `ideam_weekly.py` → `ideam_wk2.py` → `an7.py` → `an6.py` → `an8.py`; después `an9`–`an11`, `annex.py` y los `build_*`.
2. Tienen **rutas absolutas** al equipo de la autora (`...\RESPIRA - copia\data` y `...\RESPIRA\reports`).
3. Los scripts `build_stations.py`, `build_siv.py` y `build_pilot_matrix.py` **sobrescriben** entregables de `reports/quinta_auditoria/`. No ejecutarlos sin respaldo.
4. Defectos conocidos documentados, no corregidos: ver columna «Notas» de `scan_dane.py`, `an3.py` y `an5.py`.
5. Requieren Python 3.12 con pandas/numpy (los de análisis) o solo la biblioteca estándar (los de lectura). Los scripts `auditar_*` anteriores requieren además `openpyxl`, que **no estaba instalado** en este entorno.
6. La regla de calendario (4 de enero) de `ideam_weekly.py` y `an9.py` **no está confirmada por el INS**.

## A. Scripts copiados (22)

Hash SHA-256 del original = hash de la copia (verificado, 22/22).

| Script | Tipo | Finalidad | Dependencias | Escritura / borrado | Notas | SHA-256 |
|---|---|---|---|---|---|---|
| `an1.py` | Análisis | Une los nar_{año}.csv y resume SIVIGILA por año. | pandas; requiere nar_*.csv | Escribe nar_all.pkl y siv_year_summary.csv. | Rutas relativas al directorio de trabajo. | `463f4d25db9856c80ba803b6f67484aaeb84b0a760ba322734535328509a8b1c` |
| `an10.py` | Análisis | Conteo de observaciones por escenario y partición. | pandas | No escribe (imprime). | Relativas. | `2fd6682d63ee93a2ab0d19fc6496fefc1140c547b08b9686f5f955a0de682666` |
| `an11.py` | Análisis | Verificación adicional de NUM_CON y de cobertura. | pandas | No escribe (imprime). | Relativas. | `cd72a6bf6c8558a8aae19e8b165ce2149216a9c3645406865ac61e3dde5323c3` |
| `an2.py` | Análisis | Caracteriza los grupos de reporte repetido. | pandas; requiere nar_all.pkl | Escribe rep_groups.csv. | Relativas. | `4936e99a5419001e099ff2f4fcc6bae1d25305c10099baa0ed454996aceb86b0` |
| `an3.py` | Análisis | Comportamiento de NUM_CON y sensibilidad de reglas. | pandas; requiere nar_all.pkl | Escribe consol_sens.csv. Defecto conocido: la variante «max» falla (idxmax con NA); se rehízo en an4.py. | Relativas. | `192c40b09985e2acd8f717dc595976e17a74835f856b0e04427236f1e17c640b` |
| `an4.py` | Análisis | Sensibilidad de reglas de consolidación y cobertura por municipio-semana. | pandas; requiere nar_all.pkl | Escribe consol_sens.csv y siv_mun_cov.csv. | Relativas. | `82b105d2ef4780caddff0a64e0f47fb9ec1e7edae93e39840aa42d46366b6467` |
| `an5.py` | Análisis | Verifica el piloto contra SIVIGILA y calcula población 0–4 DANE. | pandas; requiere nar_all.pkl y dane_*.csv | Escribe dane_a.pkl, dane_b.pkl y pop_u5.csv. Defecto conocido: el archivo se parchó después de escribirlo para leer dane_a.csv sin encabezado. | Ruta absoluta al piloto en `RESPIRA`. | `81f8c8a975ff9b29fc0b98f1ee1289328c8f8977600c339d43fc5dfc752545e8` |
| `an6.py` | Análisis | Salto DANE 2017→2018 y cruce estación→municipio por nombre. | pandas | Escribe mun_master.csv. | Absoluta a `reports/estaciones_candidatas_ideam.csv`. No incluye los tres mapeos manuales (los añade an8.py). | `695c27d31c561e611ed6fe1a2fb19efac4467ed481a452a91c7acb0801765fe2` |
| `an7.py` | Análisis | Municipio-semana de IRA, ceros y razón IRA/consultas. | pandas | Escribe w_mun_week.pkl. | Relativas. | `ea4084da53520e349141229c50e89d587ea6bc9b99a7eb712c461522e3baea0c` |
| `an8.py` | Análisis | Disponibilidad conjunta IRA + temperatura/precipitación por municipio. | pandas; requiere w_mun_week.pkl, ideam_wk_days.pkl | Escribe station_mpio_map.csv y joint_counts.csv. | Absoluta a candidatas. Mapea Tumaco, El Tablón y Santa Cruz a mano. | `7818e7652bd74a8c85bae2b6097b3892bb3a01e604c6346eabc30d53f3f196d7` |
| `an9.py` | Validación | Recalcula la temperatura semanal del piloto y compara el calendario. | pandas, numpy | No escribe (imprime). | Absolutas. | `f04e8cef1a0fc7d3c5af55ccba2521ed7a3fe6d73350f3b5370cfa51662bcc1f` |
| `annex.py` | Generación de informe | Genera el anexo de municipios (markdown) del informe general. | pandas | Escribe annex_municipios.md en el directorio actual. | Relativas. | `db2244bc63314259c9ecddd191b88cb31dcf0240ff44e05d9db4d1cc9bcc7f0a` |
| `build_pilot_matrix.py` | Generación de informe | Construye EVALUACION_DATASET_PILOTO.csv y MATRIZ_COMPATIBILIDAD_FUENTES.csv. | pandas | **SOBRESCRIBE** ambos CSV en `reports/quinta_auditoria/`. | Ruta absoluta de salida. Contiene el texto de las evaluaciones. | `bde585e0923d52fc7580a58297246a9274473fd53235f48f7c9c6c874efad62a` |
| `build_siv.py` | Generación de informe | Construye EVALUACION_VARIABLES_SIVIGILA.csv. | pandas; requiere cols_*.json | **SOBRESCRIBE** `reports/quinta_auditoria/EVALUACION_VARIABLES_SIVIGILA.csv`. | Ruta absoluta de salida. | `d1999371ad958c6c3c336c38f5393367e028f9bfbf2fd9b91e5fde0ac28b94f0` |
| `build_stations.py` | Generación de informe | Construye EVALUACION_ESTACIONES_IDEAM.csv. | pandas | **SOBRESCRIBE** `reports/quinta_auditoria/EVALUACION_ESTACIONES_IDEAM.csv`. | Ruta absoluta de salida. No ejecutar sin respaldo. | `4cdca7ace79e57395eef80b44d9802412ac1933fc6e848c66c26a626cbc01211` |
| `dane_hdr.py` | Exploración | Imprime las primeras filas de una hoja DANE. | stdlib + xlsx_stream.py | No escribe (imprime). | Ruta absoluta. Argumentos: archivo, hoja, n filas. Falla con nombres de hoja con acentos. | `40b9f26d6929832ea853614ecc5a643349d8f1da63bc64da262eda1afd096081` |
| `dane_hdr2.py` | Exploración | Imprime las filas de encabezado del libro DANE 2018–2042. | stdlib + xlsx_stream.py | No escribe (imprime). | Ruta absoluta. | `872d82098029a2e84a5b7dc8b2b648c33efccf21f4dac6a7e10c3234cf322a4d` |
| `ideam_weekly.py` | Análisis | Cobertura semanal (≥6/7 y 7/7 días) de 165 series IDEAM 2012–2022, rachas, coherencia física. | pandas, numpy | Escribe cal.pkl, ideam_weekly.csv e ideam_consist.csv en el directorio actual. | Rutas absolutas a la copia de datos y a `reports/estaciones_candidatas_ideam.csv`. Calendario por regla del 4 de enero (no confirmado por el INS). | `527fe13737fa12868554b0543d0f52f85ad80f809175bf3d0ddcc8691bf6d3ef` |
| `ideam_wk2.py` | Análisis | Guarda días válidos por semana para cada estación-variable. | pandas; requiere cal.pkl | Escribe ideam_wk_days.pkl. | Rutas absolutas. Lento (varios minutos). | `19b20dd11f7775e01b9ea71910ef7949e722cea461ae2d4e2b9fe2c09976b98d` |
| `scan_dane.py` | Extracción | Extrae población 0–4 por sexo/edad de Nariño de los libros DANE municipales. | stdlib + xlsx_stream.py | Escribe dane_{tag}.csv, dcols_{tag}.json y dsum_{tag}.json en el directorio actual. | Ruta absoluta a `RESPIRA - copia/data`. Defecto conocido: para el libro 2005–2017 (tag a) no escribe la fila de encabezado del CSV; el análisis posterior lo lee con header=None. | `9f2d1f7be967d9f43b54376705defb17d514dcbf0a87621f8ec67e8f466ec8a7` |
| `scan_siv.py` | Extracción | Recorre la hoja de detalle de un libro SIVIGILA y extrae campos no personales de filas con cod_mun 52*. | stdlib + xlsx_stream.py | Escribe nar_{año}.csv, sum_{año}.json y cols_{año}.json en el directorio actual. | Ruta absoluta a `RESPIRA - copia/data/SIVIGILA/`. Hoja por año codificada. Argumento: año. | `87b666e4d3c43ccb4fdcc02189ab482add2eb3d807f2af379ffd65a86ef5acae` |
| `xlsx_stream.py` | Lectura | Lector XLSX en streaming (zipfile + XML, stdlib). Solo lectura. | stdlib | No escribe. | Ninguna ruta fija. Base de scan_siv/scan_dane. | `dd19ec7c3d1972d1022ef0fb7d90132f72aa5705052d2fb078b2c87d9c0a798f` |

Ninguno contiene instrucciones de borrado (`remove`, `unlink`, `rmtree`) ni se conecta a bases de datos.

## B. Scripts encontrados y NO copiados

| Script | Motivo |
|---|---|
| `hdr.py` (scratchpad de la sesión; SHA-256 `a0f7c0b6a2f0f9d40343fd9491884fd87b2675ac275f0aac2dfd759907b5e3d8`) | Vuelca las primeras filas completas de los libros SIVIGILA a JSON, incluyendo campos de contacto de las personas que diligencian (nombre, cargo, teléfono, correo). No es seguro preservarlo ni el JSON que produjo. Su única función (leer los encabezados) la cubre `scan_siv.py`. |
| `auditar_cuarta_respira.py` y `auditar_datasets_respira.py` | **Ya están en `data/scripts/`** y son idénticos (mismo SHA-256) a los de `RESPIRA - copia/data/scripts/`. No hay nada que copiar. |

Scripts descritos en los informes pero **no localizados** como archivos: ninguno que se haya podido identificar. No se reconstruyó ningún script a partir de descripciones. Un primer intento de `build_siv_pilot.py` falló al crearse (error de shell) y no existe como archivo.

## C. Scripts previos ya presentes en `data/scripts/`

| Script | SHA-256 | Tipo | Escritura | Dependencias |
|---|---|---|---|---|
| `auditar_cuarta_respira.py` | `d1de1229d7ea23e1682c0cb35e06cb368cd7deeb3bd6adc30f0d8e0ab798f2d6` | Validación (4.ª auditoría, 53 comprobaciones) | Escribe 6 CSV y un `.md` en un directorio de salida de auditoría (`sha256_fuentes.csv`, `calendario_semana_epi.csv`, `filas_repeticion_sivigila.csv`, el piloto v2, `cobertura_meteorologica.csv`, `validaciones.csv`, `resumen_validaciones.md`) | `openpyxl` (no instalado aquí), rutas por argumento |
| `auditar_datasets_respira.py` | `e77d0b66b10567517e012d93cb846dee57219cac7b09b29bf15a6a8a6f993109` | Auditoría de inventario (3.ª auditoría) | Escribe un informe `.md` (`write_text`) en el directorio indicado por `--out` (defecto `reports`) | `pandas` y `openpyxl` (no instalado aquí) |

No se modificaron.
