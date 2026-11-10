from pathlib import Path
import argparse, csv, hashlib, json, math, re, sys
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook

DEFAULT_DATA = Path(r'C:\Users\MARIA VICTORIA\Desktop\universidad\SEMESTRES\QUINTO SEMESTRE\Diseño de interfaces\FINALES\RESPIRA\data')

def xlsx_info(path):
    wb=load_workbook(path, read_only=True, data_only=True)
    out=[]
    for ws in wb.worksheets:
        headers=[]
        for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row or 1, 10), values_only=True):
            vals=[str(x) if x is not None else '' for x in row]
            if any(vals): headers.append(vals)
        out.append({'sheet':ws.title,'dimension':ws.calculate_dimension(),'rows':ws.max_row,'cols':ws.max_column,'preview':headers[-2:]})
    wb.close()
    return out

def main():
    ap=argparse.ArgumentParser(description='Auditoría exploratoria de datasets RESPIRA; solo lectura.')
    ap.add_argument('--data',type=Path,default=DEFAULT_DATA)
    ap.add_argument('--out',type=Path,default=Path('reports'))
    args=ap.parse_args(); data=args.data
    args.out.mkdir(parents=True,exist_ok=True)
    date=datetime.now().strftime('%Y%m%d')
    target=args.out/f'INFORME_AUDITORIA_DATASETS_RESPIRA_{date}.md'
    if target.exists(): target=args.out/f'INFORME_AUDITORIA_DATASETS_RESPIRA_{date}_{datetime.now():%H%M%S}.md'
    lines=['# Auditoría técnica de datasets para RESPIRA','',f'Fecha de elaboración: {datetime.now():%Y-%m-%d}. Inspección de solo lectura.','',
    '> Este informe describe los archivos disponibles en el directorio indicado. No entrena modelos, no transforma ni sobrescribe fuentes. Las dimensiones Excel se basan en metadatos del libro; los archivos SIVIGILA anuales se inspeccionan estructuralmente y no se agregan ni recalculan sus registros clínico-epidemiológicos.','',
    '## Resumen ejecutivo','',
    'Se encontraron catálogo nacional IDEAM (19.828 filas), catálogo Nariño `NARI_O.csv` (336 filas, 168 códigos distintos), una extracción de observaciones IDEAM/de terceros de 156.311 filas y el libro DANE nacional de población por área, sexo y edad. El libro DANE no contiene detalle municipal en esta hoja nacional; por tanto no permite estimar aquí población menor de 5 años por municipio. Se hallaron archivos SIVIGILA evento 995 para 2012–2022 en `data/SIVIGILA`. La extracción meteorológica observada cubre únicamente 25-10-2026 y no 2012–2022. No hay base para preparar todavía una serie semanal integrada.','',
    '## Inventario y auditoría','', '| Archivo | Tamaño | Dimensiones / estructura | Periodo | Cobertura / conclusión |','|---|---:|---|---|---|']
    files=sorted(data.glob('*'))
    for p in files:
        if p.is_file():
            n=p.name; size=p.stat().st_size
            if p.suffix.lower()=='.csv':
                try:
                    df=pd.read_csv(p,encoding='utf-8-sig',sep=None,engine='python')
                    dims=f'{len(df):,} × {len(df.columns)}'; per='No aplica / inspeccionar fechas'
                    cover='Nacional' if 'Nacional' in n or 'Cat_logo' in n or 'Datos_de_Estaciones' in n else 'Nariño'
                    if 'FechaObservacion' in df:
                        dt=pd.to_datetime(df.FechaObservacion,errors='coerce'); per=f'{dt.min()} a {dt.max()}'
                        cover=f"{df.Departamento.nunique()} departamentos; {df.Municipio.nunique()} municipios; {df.CodigoEstacion.nunique()} estaciones; {df.DescripcionSensor.nunique()} sensores"
                    lines.append(f'| `{n}` | {size:,} bytes | {dims} | {per} | {cover} |')
                except Exception as e: lines.append(f'| `{n}` | {size:,} bytes | No leído: {e} | — | Pendiente |')
            elif p.suffix.lower()=='.xlsx':
                inf=xlsx_info(p); dims='; '.join(f"{x['sheet']}: {x['rows']:,}×{x['cols']}" for x in inf)
                per='2018–2070 (nombre del libro)' if 'PPED-' in n else 'Año indicado por archivo'
                cover='Nacional por área/sexo/edad' if 'PPED-' in n else 'Nacional; evento 995'
                lines.append(f'| `{n}` | {size:,} bytes | {dims} | {per} | {cover} |')
    siv=data/'SIVIGILA'
    lines += ['', '### Catálogo IDEAM y `NARI_O.csv`','',
    'El catálogo tiene las columnas `Codigo`, `Nombre`, `Categoria`, `Tecnologia`, `Estado`, `Departamento`, `Municipio`, `Ubicación`, `Altitud`, `LONGITUD`, `LATITUD`, `Fecha_instalacion`, `Fecha_suspension`, `Area Operativa`, `Corriente`, `Area Hidrografica`, `Zona Hidrografica`, `Subzona hidrografica`, `Entidad`. CSV UTF-8 con BOM, autodetección de separador (coma), 19 columnas; tipos inferidos: códigos enteros, coordenadas flotantes, altitud entera y resto texto. Las columnas son etiquetas observadas del archivo; salvo categoría/estado geográfico, la semántica instrumental y los cambios de catálogo requieren diccionario oficial.','']
    catfile=next(iter(data.glob('Cat*IDEAM*.csv')),None)
    if catfile:
        cat=pd.read_csv(catfile,encoding='utf-8-sig',sep=None,engine='python')
        nari=cat[cat.Departamento.astype(str).str.normalize('NFKD').str.contains('Narin',case=False,na=False)]
        lines += [f"- Catálogo nacional: {len(cat):,} filas, {cat.Codigo.nunique():,} códigos distintos; estados: {cat.Estado.value_counts(dropna=False).to_dict()}.",f"- Nariño: {len(nari)} filas; {nari.Codigo.nunique()} códigos distintos; {nari.Municipio.nunique()} etiquetas municipales. `{nari.Codigo.duplicated().sum()}` filas son repeticiones de código, por lo que no deben contarse como estaciones únicas sin resolverlas.",f"- Categorías Nariño (filas): {nari.Categoria.value_counts().to_dict()}.",f"- Estados Nariño: {nari.Estado.value_counts().to_dict()}.",'- `NARI_O.csv` repite exactamente el subconjunto departamental del catálogo: no tiene fecha de observación, valor medido ni campos de sensor/unidad. No es evidencia de una serie temporal ni de medición activa.', '', 'Estaciones Nariño con categoría climatológica (candidatas, por categoría solamente; no confirma sensor ni continuidad):','', '| Código | Estación | Categoría | Estado | Municipio | Altitud m |','|---|---|---|---|---|---:|']
        shortlist=nari[nari.Categoria.astype(str).str.contains('Climatol',case=False,na=False)].drop_duplicates('Codigo')
        for _,r in shortlist.iterrows(): lines.append(f"| {r.Codigo} | {r.Nombre} | {r.Categoria} | {r.Estado} | {r.Municipio} | {r.Altitud} |")
        lines += ['', 'Candidatas de precipitación por categoría (`Pluviométrica`/`Pluviográfica`), no garantía de disponibilidad: ', ', '.join(f"{r.Codigo} {r.Nombre} ({r.Municipio}, {r.Estado})" for _,r in nari[nari.Categoria.astype(str).str.contains('Pluvi',case=False,na=False)].drop_duplicates('Codigo').head(30).iterrows()),'. El catálogo no contiene una variable observada, frecuencia, medición individual ni fechas de cobertura histórica; estaciones activas tampoco garantizan cobertura histórica.', '']
    obsfile=next(iter(data.glob('Datos_de_Estaciones*.csv')),None)
    if obsfile:
        obs=pd.read_csv(obsfile,encoding='utf-8-sig',sep=None,engine='python')
        dt=pd.to_datetime(obs.FechaObservacion,errors='coerce')
        nr=obs[obs.Departamento.astype(str).str.normalize('NFKD').str.contains('Narin',case=False,na=False)]
        lines += ['### CSV de observaciones IDEAM/de terceros','', '{}: {} x {}; columnas {}. Periodo {} a {}; marcas {}. Estaciones {}; sensores {}; descripciones {}; celdas vacias {}. Filas Nariño {}; estaciones Nariño {}. Solo corte de 25-10-2026; no sirve para serie 2012-2022.'.format(obsfile.name,len(obs),len(obs.columns),list(obs.columns),dt.min(),dt.max(),dt.nunique(),obs.CodigoEstacion.nunique(),obs.CodigoSensor.nunique(),obs.DescripcionSensor.nunique(),int(obs.isna().sum().sum()),len(nr),nr.CodigoEstacion.nunique()),'', 'Principales descripciones de sensor:','']
        for k,v in obs.DescripcionSensor.value_counts().head(20).items(): lines.append(f'- {k}: {v:,}')
        if len(nr):
            lines += ['', 'Cobertura del corte en Nariño por descripción (cantidad de estaciones; no periodo histórico):', '']
            for k,v in nr.groupby('DescripcionSensor').CodigoEstacion.nunique().sort_values(ascending=False).items():
                lines.append(f'- {k}: {v} estaciones')
            lines += ['', 'Estaciones Nariño con sensores útiles presentes en este corte (precipitación/temperatura/humedad):', '']
            useful=nr[nr.DescripcionSensor.astype(str).str.contains('Precipit|Temperatura del aire|Temperatura m.nima del Aire|Temperatura m.xima del Aire|Humedad relativa del aire',case=False,na=False)]
            for (code,name),g in useful.groupby(['CodigoEstacion','NombreEstacion']):
                sensors=', '.join(sorted(set(str(x) for x in g.DescripcionSensor if pd.notna(x))))
                lines.append(f'- {code} — {name}: {sensors}')
        lines += ['', '### Población DANE','',
        'El libro `PPED-AreaSexoEdadNac-2018-2070.xlsx` contiene hojas de índice y presentación, y una hoja de serie **Nacional** por área, sexo y edad. En la tabla, las filas son territorio × año × área; las edades simples están desglosadas por sexo y existe bloque `Total` por edad. Para población 0–4 nacional debe usarse exclusivamente el bloque Total 0, 1, 2, 3, 4; alternativamente sumar ambos sexos, nunca ambos y Total a la vez. “Cabecera”, “Centros Poblados y Rural Disperso” y “Total” son categorías no aditivas entre sí: usar solo Total para población nacional.','',
        'La hoja contiene filas de datos para `Total Nacional` por área; no aparecen departamentos ni municipios entre los registros de datos. No incluye municipios ni códigos DIVIPOLA; por tanto no es posible calcular de forma fiable población municipal menor de cinco años para Nariño en 2018, 2022 o 2025. Hace falta el anexo municipal DANE por área, sexo y edad simple del periodo correspondiente. Aunque el archivo se titula 2018–2070, validar dentro de la hoja y metadatos las filas/años disponibles antes de uso. La nota de actualización indica 18-07-2025.','']
    lines += ['### SIVIGILA evento 995','']
    for p in sorted(siv.glob('Datos_*_995.xlsx')):
        wb=load_workbook(p,read_only=True,data_only=True)
        info=[]
        for ws in wb.worksheets:
            rowidx=1; row=next(ws.iter_rows(min_row=1,max_row=1,values_only=True))
            for candidate in range(1,min(ws.max_row or 1,5)+1):
                r=next(ws.iter_rows(min_row=candidate,max_row=candidate,values_only=True))
                if any(str(x).strip().lower() in ('cod_eve','fec_not','semana') for x in r if x is not None):
                    rowidx=candidate; row=r; break
            info.append((ws.title,ws.max_row,ws.max_column,[str(x) for x in row],rowidx))
        lines.append(f"- `{p.name}` ({p.stat().st_size:,} bytes): "+'; '.join(f"hoja {name}, {rows:,} filas × {cols}, encabezados fila {rowidx}, {len(headers)} campos: `{', '.join(headers[:20])}{'…' if len(headers)>20 else ''}`" for name,rows,cols,headers,rowidx in info))
        wb.close()
    lines += ['', '2012 contiene hojas `995 52` y `Base Recibida`; 2013–2018 tienen una hoja principal con nombres variables; 2019 incluye `Hoja1` (resumen agregado) y `Final` (detalle); 2020 usa `995_2020_Depurada`; 2021 `ACUMULADO`; 2022 `995`. Se detectó encabezado en fila 2 para 2021 (fila 1 tiene rótulos parciales), y la hoja alcanza exactamente el límite de 1.048.576 filas de Excel: revisar si está truncada. Una fila de muestra presenta `fec_not=2022-01-01`, `año=2021`, `semana=52`, lo que amerita validar calendario/cierre y fecha de notificación. En `2019`, no mezclar `Hoja1` agregada con `Final` detallada. En muestra se observan `cod_eve`, `fec_not`, `semana`, `año`, `cod_pre`, `cod_sub`, `cod_mun`, `num_con`, `demanda`, `grupoh_*`, `hospital_*`, `tot_irag` (variación de campos entre años). `cod_mun` parece código DIVIPOLA de cinco dígitos en la hoja Base Recibida, pero debe verificarse por diccionario y normalizarse como texto con ceros iniciales; `cod_pre` parece prestador/UPGD, no municipio de residencia. No se asigna significado clínico a cada sufijo por nombre solamente. Según protocolo INS 2024, morbilidad IRA evento 995 es notificación colectiva semanal, con numeradores y denominadores basados en búsqueda RIPS; no equivale a personas únicas ni casos individuales. Verificar definición histórica por año, fecha efectiva y tipo de población antes de calcular menores de 5. No se agregaron registros ni se auditaron valores/duplicados de las 11 bases; ese análisis requerirá reglas de datos y validación de columnas.','',
    '## Compatibilidad geográfica y temporal','',
    'No se construyó una matriz municipal completa porque el libro DANE disponible es nacional y el catálogo meteorológico no codifica municipios DIVIPOLA. Los archivos SIVIGILA sí traen `cod_mun` y `cod_pre`, pero su significado y la localidad notificada/residencia/ocurrencia requieren diccionario INS y validación. La unión por nombre aproximado no es aceptable. Usar DIVIPOLA como texto y una tabla oficial vigente/histórica para cambios territoriales. IDEAM presenta municipio como texto; resolverlo mediante catálogo y código geográfico validado antes de unir.','',
    '| Fuente | Periodo comprobado | Granularidad | Aporta a dataset semanal 2012–2022 |','|---|---|---|---|',
    '| IDEAM catálogo / `NARI_O.csv` | Fechas de instalación/suspensión, no observaciones | Estación | Parcial: mapa de estaciones potenciales; cobertura de variables no comprobada |',
    '| Observaciones IDEAM/terceros | 25-10-2026 | Estación-sensor-observación (intervalos subdiarios) | No para entrenamiento histórico 2012–2022 |',
    '| DANE | Proyección 2018–2070 declarada; hoja nacional | Año × área × sexo × edad | No por municipio con archivo presente |',
    '| SIVIGILA 995 | Archivos anuales 2012–2022; campos fec_not/semana | Agregado colectivo notificante/municipio según validación | Potencialmente sí, tras diccionario, población etaria y calidad |','',
    '## Evaluación para RESPIRA','',
    '| Variable candidata | Estado | Observación |','|---|---|---|',
    '| Año/semana epidemiológica | Parcialmente disponible | `semana`, `año` en SIVIGILA; validar calendario epidemiológico, semanas faltantes y cambios de formato. |',
    '| Municipio DIVIPOLA | Pendiente de validar | `cod_mun` en SIVIGILA; catálogo IDEAM da nombres; anexo municipal DANE ausente. |',
    '| IRA <5 años | Pendiente de validar | Evento colectivo; significados de grupos edad y tipo de servicio/denominador deben verificarse por año. |',
    '| Temperatura máxima/mínima, precipitación, humedad | Parcial/ausente históricamente | Sensor descriptions existen en snapshot 2026, pero no hay historia 2012–2022. |',
    '| Población municipal <5 | Ausente en archivo presente | Libro DANE nacional solamente. |',
    '| Variables semanales derivadas | Pendiente | Requiere originales de observación multianuales, agregación temporal validada y reglas de datos faltantes. |','',
    'Horizontes futuros: para semana objetivo `t+h`, definir por separado un objetivo a 1, 2 y 3 semanas usando la métrica IRA validada en semana `t+h`; comparar alerta de umbral o cambio relativo contra una línea base, sin mezclar consultas, hospitalizaciones, UCI y muertes. Cada predictor debe limitarse a información disponible al momento de emitir alerta. La fecha de notificación (`fec_not`) no necesariamente es fecha de ocurrencia; el retraso de reporte debe modelarse/medirse.','',
    '2012–2022 podría permitir una prueba histórica epidemiológica exploratoria si se obtienen datos meteorológicos de ese periodo y se resuelven cambios de formulario/definición, completitud y geografía. No se puede afirmar suficiencia predictiva con los archivos actuales.','',
    '## Riesgos y pendientes','',
    '- Repetición de 168 códigos en las 336 filas Nariño: revisar duplicados de catálogo antes de contar estaciones y distinguir múltiples sensores/versiones o registros repetidos.',
    '- `NARI_O.csv` no observa tiempo meteorológico; no confundir catálogos con datos medidos.',
    '- Los datos observados disponibles son un corte contemporáneo de horas de 2026, por lo que no resuelven retroalimentación temporal histórica, consistencia ni completitud anual.',
    '- No se identificó DIVIPOLA en DANE porque el detalle municipal no está en el libro actual; código numérico puede perder cero inicial si se trata como entero.',
    '- Distintas estructuras de pestañas/campos en SIVIGILA por año; el segundo tab Base Recibida puede diferir de la pestaña publicada. Debe definirse cuál es el extracto autoritativo.',
    '- El catálogo no permite validar físicamente coordenadas ni altitud sin límites oficiales y referencias; no se han supuesto rangos como evidencia de invalidez.',
    '- Para estaciones cercanas, la asociación municipal requiere distancia, altitud, barreras topográficas y cobertura. No se propone una asignación automática.',
    '- Riesgo de fuga temporal: no usar observaciones/denominadores que no estarían disponibles al emitir alerta; separar fecha de ocurrencia, notificación y disponibilidad.','',
    '## Próximos pasos priorizados','',
    '1. Solicitar/ubicar la serie IDEAM histórica diaria u horaria 2012–2022 con códigos de estación, fecha, variable, unidad y flags de calidad; verificar las candidatas climatológicas y pluviométricas de Nariño.',
    '2. Obtener el archivo DANE municipal por área, sexo y edad simple y validar cobertura por municipio/año; sumar edades 0–4 únicamente en área Total y ambos sexos o bloque Total.',
    '3. Conseguir diccionario de datos/formatos SIVIGILA evento 995 de cada año y confirmar semántica de `cod_mun`, `cod_pre`, grupos de edad, `demanda`/`num_con` y la pestaña analítica autorizada.',
    '4. Obtener DIVIPOLA oficial/histórica y definir claves canónicas en texto para cada fuente.',
    '5. Luego de validar definiciones, perfilar duplicados, vacíos, semanas y completitud estación-variable-año por bloques; construir matriz municipal de cobertura con asociaciones de estaciones revisadas.',
    '6. Solo después diseñar objetivos de horizonte 1–3 semanas y esquema de validación temporal; no entrenar aún.','',
    '## Documentación externa consultada (2026-10-25)','',
    '- DANE, Proyecciones de población 2018–2070 / actualización de 18-07-2025: https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion',
    '- DANE, DIVIPOLA: https://www.dane.gov.co/index.php/sistema-estadistico-nacional-sen/normas-y-estandares/nomenclaturas-y-clasificaciones/nomenclaturas/codificacion-de-la-division-politica-administrativa-de-colombia-divipola',
    '- INS, Protocolo IRA 2024 (incluye evento 995, notificación colectiva semanal y numeradores/denominadores RIPS): https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_IRA%202024.pdf',
    '- IDEAM: no se consultó documentación de definición instrumental/estándar de los campos del catálogo en esta inspección; significado de sensores por categoría queda pendiente de confirmar.','',
    '## Reproducibilidad','',
    'Script de auditoría: `scripts/auditar_datasets_respira.py`. Uso: `python scripts/auditar_datasets_respira.py --data "<carpeta data>" --out reports`. Solo lee CSV/XLSX y escribe un informe con nueva fecha; no modifica los archivos fuente. El análisis SIVIGILA actual es estructural, no una validación exhaustiva registro por registro.','']
    target.write_text('\n'.join(lines),encoding='utf-8')
    print(target.resolve())
if __name__=='__main__': main()
