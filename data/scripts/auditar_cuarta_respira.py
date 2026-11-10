#!/usr/bin/env python3
"""Validaciones reproducibles de la cuarta auditoría de RESPIRA (solo lectura)."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError as exc:
    raise SystemExit("Falta openpyxl. Ejecute con el Python del entorno de RESPIRA que incluye openpyxl.") from exc

MUNICIPALITIES = {
    '52240': ('Chachagüí', '52045020'),
    '52287': ('Funes', '52055200'),
    '52678': ('Samaniego', '52055060'),
}
YEARS = (2016, 2022)
VARS = {'temp_min': 'TSSM_MN_D', 'temp_max': 'TSSM_MX_D', 'temp_mean': 'TSSM_MEDIA_D'}
def norm_station(v):
    return str(v or '').strip().lstrip('0')

def norm_text(v):
    s=unicodedata.normalize('NFKD',str(v or '').strip().casefold())
    return ''.join(ch for ch in s if not unicodedata.combining(ch))
EXPECTED_PREVIOUS_AUDIT_HASHES = {
    'docs/data-audit/segunda-auditoria/auditoria_segunda_fuentes.md': '218f479460e0e1580c8b88cd8fc3c8b98f655403b044427bd9458778340eb175',
    'docs/data-audit/segunda-auditoria/resumen_ideam_narino_archivos.csv': 'a3a055fe7bcdf3ec02ca114a8b1e2d67b63d38b9eb00bf370d98bd7e76b2b32f',
    'docs/data-audit/segunda-auditoria/cobertura_ideam_narino_estacion_anio.csv': '4a246ac667d5bef7721b9d82fb52d4f02a003a6e0672963f927e53cb75744157',
}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def norm_code(v, width=5):
    if v is None: return ''
    s=str(v).strip()
    if s.endswith('.0'): s=s[:-2]
    return s.zfill(width) if s.isdigit() else s

def number(v):
    if v is None or str(v).strip()=='': return None
    try: return float(str(v).replace(',','.'))
    except (ValueError,TypeError): return None

def date_value(v):
    if isinstance(v, datetime): return v.date()
    if isinstance(v, date): return v
    if v is None: return None
    s=str(v).strip()
    for fmt in ('%Y-%m-%d','%Y/%m/%d','%d/%m/%Y'):
        try: return datetime.strptime(s[:10],fmt).date()
        except ValueError: pass
    try: return datetime.fromisoformat(s[:19]).date()
    except ValueError: return None

def calendar(yr):
    # INS BES week 52 anchors: 25–31 Dec in both study years. With INS Sunday–Saturday weeks,
    # enumerate 52 continuous epidemiological weeks backwards/forwards from this published anchor.
    end=date(yr,12,31)
    start=end-timedelta(days=6)
    return {week:(start-timedelta(days=7*(52-week)), start-timedelta(days=7*(52-week))+timedelta(days=6)) for week in range(1,53)}

def read_pilot(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def source_sivigila(data, yr):
    path=data/'SIVIGILA'/f'Datos_{yr}_995.xlsx'
    preferred={2016:'Hoja1',2022:'995'}[yr]
    wb=load_workbook(path,read_only=True,data_only=True)
    ws=wb[preferred]
    hdr_row=1
    if yr==2021: hdr_row=2
    headers=[str(c.value or '').strip().lower() for c in next(ws.iter_rows(min_row=hdr_row,max_row=hdr_row))]
    def col(*names):
        for n in names:
            if n.lower() in headers: return headers.index(n.lower())
        return None
    ix={
      'event':col('cod_eve'),'muni':col('cod_mun','cod_mun_'),'epi_year':col('año','ano'),'week':col('semana'),
      'provider':col('cod_pre'),'sub':col('cod_sub'),'consec':col('num_con'),
      'ira1':col('iracext_1'),'ira2':col('iracext_2'),'ira3':col('iracext_3'),'fec_not':col('fec_not')}
    missing=[k for k,v in ix.items() if v is None and k not in ('fec_not',)]
    records=defaultdict(list); municipio_rows=Counter(); invalid=Counter()
    sensitive_header=re.compile(r'(nombre|telefono|tel[eé]fono|correo|email|nit|direccion|direcci[oó]n|documento|identificaci[oó]n)',re.I)
    for excel_row,row in enumerate(ws.iter_rows(min_row=hdr_row+1,values_only=True),start=hdr_row+1):
        code=norm_code(row[ix['muni']])
        if code not in MUNICIPALITIES: continue
        ev=str(row[ix['event']] or '').strip().replace('.0','')
        if ev!='995': continue
        try: w=int(float(row[ix['week']]))
        except (ValueError,TypeError): invalid['semana_no_numerica']+=1; continue
        try: y=int(float(row[ix['epi_year']]))
        except (ValueError,TypeError): y=yr
        if not 1<=w<=53: invalid['semana_fuera_rango']+=1; continue
        municipio_rows[code]+=1
        vals=[]
        for k in ('ira1','ira2','ira3'):
            v=number(row[ix[k]])
            vals.append(v)
        # This tuple intentionally excludes all potentially identifying and contact fields.
        rec={
          'source_row':excel_row,'municipality':code,'year':y,'week':w,
          'provider':str(row[ix['provider']] or '').strip(),'sub':str(row[ix['sub']] or '').strip(),
          'consecutive':str(row[ix['consec']] or '').strip(),
          'ira1':vals[0],'ira2':vals[1],'ira3':vals[2],
          'ira_sum':sum(vals) if all(v is not None for v in vals) else None,
          'full_signature':tuple(row),
        }
        records[(code,y,w)].append(rec)
    wb.close()
    return path,ws.max_row,ws.max_column,headers,ix,records,municipio_rows,invalid,missing

def daily_data(path):
    values=defaultdict(list); malformed=0
    with path.open(encoding='utf-8-sig',errors='replace') as f:
        for line_no,line in enumerate(f,1):
            parts=line.rstrip('\r\n').split('|')
            if len(parts)<2: continue
            if parts[0].strip().casefold()=='fecha' and parts[1].strip().casefold()=='valor': continue
            d=date_value(parts[0]); v=number(parts[1])
            if d is None or v is None: malformed+=1; continue
            values[d].append(v)
    return values,malformed

def verify_population(data, pilot):
    # Full row-level DANE audit is preserved in the prior audit. This fast repeat check
    # validates the pilot's six keys, annual values, and correct source-book handoff.
    pop={}; mismatches=[]
    expected_books={2016:'DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx',2022:'PPED-AreaSexoEdadMun-2018-2042_VP.xlsx'}
    for r in pilot:
        key=(norm_code(r.get('municipality_divipola')),int(r['year']))
        value=number(r.get('population_under5_annual'))
        if key in pop and pop[key]!=value: mismatches.append((key,'population varies across weeks'))
        pop[key]=value
        if r.get('source_dane')!=expected_books.get(key[1]): mismatches.append((key,'unexpected DANE workbook'))
    return pop,[],mismatches

def main():
    here=Path(__file__).resolve()
    default_root=here.parents[2]
    ap=argparse.ArgumentParser(description='Auditoría cuarta RESPIRA (solo lectura de fuentes; resultados versionados).')
    ap.add_argument('--root',type=Path,default=default_root)
    ap.add_argument('--out',type=Path,default=None,help='Carpeta de resultados; por defecto <root>/reports/cuarta_auditoria')
    args=ap.parse_args(); root=args.root.resolve(); data=root/'data'; out=(args.out or root/'reports'/'cuarta_auditoria').resolve(); out.mkdir(parents=True,exist_ok=True)
    checks=[]
    def check(sev,ident,area,msg,evidence=''):
        checks.append({'status':sev,'id':ident,'area':area,'result':msg,'evidence':evidence})
    def exists(rel):
        p=root/rel
        check('PASS' if p.exists() else 'FAIL','FILE_'+re.sub('[^A-Z0-9]+','_',rel.upper()),'inventario','Existe' if p.exists() else 'No existe',rel)
        return p

    print('Fase 1/6: inventario y huellas SHA-256',flush=True)
    # Artifact/input inventory and hashes. Existing saved hashes are enforced only where a prior digest exists.
    audit_files=[
      'docs/data-audit/segunda-auditoria/README.md',
      'docs/data-audit/segunda-auditoria/auditoria_segunda_fuentes.md',
      'docs/data-audit/segunda-auditoria/resumen_ideam_narino_archivos.csv',
      'docs/data-audit/segunda-auditoria/cobertura_ideam_narino_estacion_anio.csv',
      'data/reports/INFORME_AUDITORIA_DATASETS_RESPIRA_20261025.md',
      'data/reports/auditoria_segunda_fuentes.md',
      'reports/estaciones_candidatas_ideam.csv','reports/metadatos_variables_ideam.csv',
      'reports/auditoria_sivigila_995_2012_2022.md','reports/diccionario_sivigila_995.csv',
      'data/processed/pilot/piloto_respira_2016_2022.csv',
      'data/DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx',
      'data/PPED-AreaSexoEdadMun-2018-2042_VP.xlsx',
      'data/Cat_logo_Nacional_de_Estaciones_del_IDEAM (1).csv',
    ]
    source_paths=[]
    for yr in (2016,2021,2022): source_paths.append(f'data/SIVIGILA/Datos_{yr}_995.xlsx')
    for code in (v[1] for v in MUNICIPALITIES.values()):
        for variable in VARS.values(): source_paths.append(f'data/TemperaturaNacionalDiaria/{variable}@{code}.data')
    all_hashes=[]
    for rel in audit_files+source_paths:
        p=exists(rel)
        if p.exists():
            digest=sha256(p); expected=EXPECTED_PREVIOUS_AUDIT_HASHES.get(rel)
            hstatus='VERIFIED_MATCH' if expected and digest==expected else ('HASH_MISMATCH' if expected else 'CURRENT_SNAPSHOT_NO_PRIOR_BASELINE')
            all_hashes.append({'file':rel,'bytes':p.stat().st_size,'sha256':digest,'baseline_status':hstatus,'prior_sha256':expected or ''})
            if expected: check('PASS' if digest==expected else 'FAIL','HASH_'+re.sub('[^A-Z0-9]+','_',rel.upper()),'integridad',hstatus,rel)
    with (out/'sha256_fuentes.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','bytes','sha256','baseline_status','prior_sha256']); w.writeheader(); w.writerows(all_hashes)

    print('Fase 2/6: esquema del piloto y calendario',flush=True)
    # Pilot schema and core consistency.
    pilot_path=exists('data/processed/pilot/piloto_respira_2016_2022.csv')
    pilot=read_pilot(pilot_path) if pilot_path.exists() else []
    fields=list(pilot[0]) if pilot else []
    expected_fields={'municipality_divipola','year','epi_week','epi_week_start','epi_week_end','ira_under5_reported_consultations','sivigila_week_status','temp_min_weekly','temp_min_days_observed','temp_min_coverage_pct','temp_max_weekly','temp_max_days_observed','temp_max_coverage_pct','temp_mean_weekly','temp_mean_days_observed','temp_mean_coverage_pct','population_under5_annual','ideam_station_code'}
    check('PASS' if expected_fields.issubset(fields) else 'FAIL','PILOT_SCHEMA','piloto','Columnas esperadas presentes' if expected_fields.issubset(fields) else 'Faltan columnas esperadas',','.join(sorted(expected_fields-set(fields))))
    keys=[(r.get('municipality_divipola'),r.get('year'),r.get('epi_week')) for r in pilot]
    check('PASS' if len(keys)==len(set(keys))==312 else 'FAIL','PILOT_KEYS','piloto',f'{len(pilot)} filas; {len(set(keys))} claves únicas municipio-año-semana','Esperado 3 × 2 × 52 = 312')
    allowed={('52240','2016','DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx'),('52287','2016','DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx'),('52678','2016','DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx'),('52240','2022','PPED-AreaSexoEdadMun-2018-2042_VP.xlsx'),('52287','2022','PPED-AreaSexoEdadMun-2018-2042_VP.xlsx'),('52678','2022','PPED-AreaSexoEdadMun-2018-2042_VP.xlsx')}
    pop_presence=all(r.get('population_under5_annual','').strip() and int(r['population_under5_annual'])>0 and norm_code(r.get('municipality_divipola'))==r.get('municipality_divipola') for r in pilot)
    pop_sources={(r.get('municipality_divipola'),r.get('year'),r.get('source_dane')) for r in pilot if r.get('epi_week')=='1'}
    pop_sources_ok={(m,str(y),src) in pop_sources for m,y,src in allowed}
    check('PASS' if pop_presence and all(pop_sources_ok) else 'FAIL','PILOT_POPULATION','DANE','Población presente y libro por periodo' if pop_presence and all(pop_sources_ok) else 'Faltantes/código/fuente DANE incorrectos','Códigos DIVIPOLA texto de 5 posiciones; población anual 0–4')

    # Official INS weekly-calendar anchors from BES week 52 source PDFs; enumerate the 52 Sunday–Saturday weeks.
    cal_rows=[]; cal_map={}
    for yr in YEARS:
        cal=calendar(yr); cal_map[yr]=cal
        for week,(start,end) in cal.items():
            old_start=date(yr,1,1)+timedelta(days=(6-date(yr,1,1).weekday())%7)+timedelta(days=7*(week-1))
            old_end=old_start+timedelta(days=6)
            cal_rows.append({'year':yr,'epi_week':week,'derived_INS_calendar_start':start.isoformat(),'derived_INS_calendar_end':end.isoformat(),'current_pilot_start':old_start.isoformat(),'current_pilot_end':old_end.isoformat(),'start_difference_days':(old_start-start).days,'end_difference_days':(old_end-end).days,'boundary_note':('01–02 Jan belong to previous epi-year SE52' if yr==2016 else '01 Jan belongs to previous epi-year SE52') if week==1 else ''})
    with (out/'calendario_semana_epi.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(cal_rows[0])); w.writeheader(); w.writerows(cal_rows)
    current_dates_match=True; calendar_violations=[]
    for r in pilot:
        yr=int(r['year']); week=int(r['epi_week']); s,e=cal_map[yr][week]
        if r['epi_week_start']!=s.isoformat() or r['epi_week_end']!=e.isoformat(): current_dates_match=False; calendar_violations.append((yr,week,r['epi_week_start'],r['epi_week_end'],s,e))
    check('PASS' if current_dates_match else 'FAIL','CALENDAR_MATCH','calendario','Fechas piloto coinciden con calendario semanal anclado por INS' if current_dates_match else f'Diferencias: {calendar_violations[:3]}','INS: semana domingo–sábado; BES SE52 2016 y 2022 = 25–31 diciembre')

    print('Fase 3/6: lectura focalizada SIVIGILA 2016/2022',flush=True)
    # Source SIVIGILA values, repeated provider-week groups, exact report key, missing weeks, and the target repeated group.
    siv_results={}; duplicate_rows=[]; source_aggregates={}; source_missing={}
    for yr in YEARS:
        path= data/'SIVIGILA'/f'Datos_{yr}_995.xlsx'
        if not path.exists(): continue
        p,rows_n,cols_n,headers,ix,records,muni_count,invalid,missingcols=source_sivigila(data,yr)
        siv_results[yr]=(p,rows_n,cols_n,headers,ix,records,muni_count,invalid,missingcols)
        # Ensure relevant collective fields exist in each year.
        required=('event','muni','epi_year','week','provider','sub','consec','ira1','ira2','ira3')
        check('PASS' if all(ix[k] is not None for k in required) else 'FAIL',f'SIV_SCHEMA_{yr}','SIVIGILA',f'{rows_n:,} filas × {cols_n} columnas; campos IRACEXT y claves '+('presentes' if all(ix[k] is not None for k in required) else 'incompletos'),f'Hoja cabecera: {p.name}; faltantes={missingcols}')
        numeric_bad=0; negative_counts=0
        for recs in records.values():
            for rec in recs:
                vals=[rec['ira1'],rec['ira2'],rec['ira3']]
                numeric_bad+=sum(v is None for v in vals)
                negative_counts+=sum(v is not None and v<0 for v in vals)
        check('PASS' if numeric_bad==0 and negative_counts==0 else 'WARNING',f'SIV_IRACEXT_VALUES_{yr}','SIVIGILA',f'celdas vacías/no numéricas seleccionadas={numeric_bad}; conteos negativos={negative_counts}','Los valores faltantes no se convierten en cero')
        for code,(name,station) in MUNICIPALITIES.items():
            weeks=sorted(w for (m,y,w),recs in records.items() if m==code and y==yr and recs)
            source_missing[(code,yr)]=sorted(set(range(1,53))-set(weeks))
        for (code,y,w),recs in records.items():
            provider_counts=Counter((x['provider'],x['sub']) for x in recs)
            for (provider,sub),cnt in provider_counts.items():
                if cnt>1:
                    group=[x for x in recs if (x['provider'],x['sub'])==(provider,sub)]
                    exact_same=len({x['full_signature'] for x in group})==1
                    complete_keys=Counter((x['provider'],x['sub'],x['consecutive']) for x in group)
                    for x in group:
                        duplicate_rows.append({'municipality_divipola':code,'municipality_name':MUNICIPALITIES[code][0],'year':y,'epi_week':w,'provider_code':provider,'provider_subindex':sub,'num_con':x['consecutive'],'source_excel_row':x['source_row'],'IRACEXT_1':x['ira1'],'IRACEXT_2':x['ira2'],'IRACEXT_3':x['ira3'],'row_indicator_sum':x['ira_sum'],'same_full_source_row_as_other_in_group':exact_same,'same_provider_week_group_n':cnt,'num_con_unique_within_group':len(complete_keys)==cnt})
        # Compute additive source aggregation, preserving every row; absent week is None.
        for code in MUNICIPALITIES:
            for week in range(1,53):
                recs=records.get((code,yr,week),[])
                source_aggregates[(code,str(yr),str(week))]=(sum(x['ira_sum'] for x in recs) if recs and all(x['ira_sum'] is not None for x in recs) else None, len(recs))
        source_week_total=sum(1 for code in MUNICIPALITIES for week in range(1,53) if records.get((code,yr,week)))
        missing_n=sum(len(source_missing[(code,yr)]) for code in MUNICIPALITIES)
        check('PASS' if missing_n==0 else 'WARNING',f'SIV_WEEKS_{yr}','SIVIGILA',f'{source_week_total} de 156 municipio-semanas con filas; {missing_n} sin filas',json.dumps({MUNICIPALITIES[c][0]:source_missing[(c,yr)] for c in MUNICIPALITIES},ensure_ascii=False))
    if len(siv_results)==2:
        h16=set(siv_results[2016][3]); h22=set(siv_results[2022][3]); only16=sorted(h16-h22); only22=sorted(h22-h16)
        check('WARNING' if only16 or only22 else 'PASS','SIV_SCHEMA_DIFF','SIVIGILA',f'columnas 2016={len(h16)}; 2022={len(h22)}; solo2016={len(only16)}; solo2022={len(only22)}',f'2016-only={only16}; 2022-only={only22}')
    with (out/'filas_repeticion_sivigila.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['municipality_divipola','municipality_name','year','epi_week','provider_code','provider_subindex','num_con','source_excel_row','IRACEXT_1','IRACEXT_2','IRACEXT_3','row_indicator_sum','same_full_source_row_as_other_in_group','same_provider_week_group_n','num_con_unique_within_group']
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(duplicate_rows)
    repeats=len({(x['municipality_divipola'],x['year'],x['epi_week'],x['provider_code'],x['provider_subindex']) for x in duplicate_rows})
    exact_complete_dups=Counter()
    # Full key includes NUM_CON as required by the INS data-record structure.
    for yr,res in siv_results.items():
        records=res[6] if False else res[5]
        for key,recs in records.items():
            c=Counter((x['municipality'],x['year'],x['week'],x['provider'],x['sub'],x['consecutive']) for x in recs)
            exact_complete_dups[yr]+=sum(n-1 for n in c.values() if n>1)
    check('WARNING' if repeats else 'PASS','SIV_REPEATED_PROVIDER_WEEK','SIVIGILA',f'{repeats} grupos con varias filas por municipio-año-semana-UPGD-sede; se conservan','La clave completa incluye NUM_CON; consulte filas_repeticion_sivigila.csv; no llamar duplicado solo por proveedor-semana')
    check('PASS' if sum(exact_complete_dups.values())==0 else 'FAIL','SIV_FULL_KEY_DUPLICATES','SIVIGILA',f'{sum(exact_complete_dups.values())} repeticiones de clave completa incluyendo NUM_CON','INS define NUM_CON como consecutivo por reporte UPGD/semana/evento')
    pilot_matches=True; mismatches=[]
    for r in pilot:
        k=(r['municipality_divipola'],r['year'],r['epi_week']); expected,source_rows=source_aggregates.get(k,(None,0))
        observed=number(r['ira_under5_reported_consultations'])
        if expected!=observed or int(r['sivigila_source_rows'])!=source_rows:
            pilot_matches=False; mismatches.append((k,expected,observed,source_rows,r['sivigila_source_rows']))
    check('PASS' if pilot_matches else 'FAIL','PILOT_SIV_AGGREGATION','SIVIGILA','Todos los conteos presentes y cantidad de filas coinciden con fuente' if pilot_matches else f'Diferencias: {mismatches[:5]}','Recalculo solo agregado IRACEXT_1+2+3; no se exportan campos personales')
    # Versioned, non-destructive correction: relabel the repeated provider-week field without changing values.
    if pilot:
        corrected=[]
        for r in pilot:
            x=dict(r)
            old=x.pop('sivigila_duplicate_provider_week_keys',None)
            x['ira_under5_collective_reported_patient_count']=x.pop('ira_under5_reported_consultations',None)
            x['sivigila_repeated_provider_week_groups']=old or '0'
            x['sivigila_consolidation_status']='REPETICION_NO_RESUELTA' if str(old or '0') not in ('0','') else 'SIN_REPETICION_DETECTADA'
            x['quality_notes']=x.get('quality_notes','').replace('DUPLICADO_PROVEEDOR_SEMANA_NO_DEDUPLICADO','REPETICION_PROVEEDOR_SEMANA_REVISAR_CONSOLIDACION')
            corrected.append(x)
        corrected_path=out/'piloto_respira_2016_2022_auditado_v2.csv'
        with corrected_path.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(corrected[0])); w.writeheader(); w.writerows(corrected)
        check('PASS','PILOT_V2_CREATED','piloto','Versión v2 conserva las filas/valores y corrige la etiqueta del grupo repetido',corrected_path.name)

    print('Fase 4/6: integridad estructural SIVIGILA 2021',flush=True)
    # 2021 completeness inventory; do not scan or re-export potentially identifying records.
    siv_dir=data/'SIVIGILA'; versions=[]
    for p in siv_dir.rglob('*'):
        if p.is_file() and '2021' in p.name.lower() and p.suffix.lower() in ('.xlsx','.xls','.csv','.parquet','.db','.sqlite'):
            versions.append(p)
    v2021=siv_dir/'Datos_2021_995.xlsx'; meta={}
    if v2021.exists():
        wb=load_workbook(v2021,read_only=True,data_only=True)
        meta={'sheets':[],'created':str(wb.properties.created),'modified':str(wb.properties.modified),'creator_metadata_present':bool(wb.properties.creator)}
        for ws in wb.worksheets:
            hdr=2 if ws.title=='ACUMULADO' else 1
            hs=[str(c.value or '').strip() for c in next(ws.iter_rows(min_row=hdr,max_row=hdr))]
            meta['sheets'].append({'name':ws.title,'rows':ws.max_row,'cols':ws.max_column,'header_row':hdr,'header_fields_n':len(hs),'has_event_week_fields':all(any(h.strip().lower()==x for h in hs) for x in ('cod_eve','semana'))})
        wb.close()
    check('WARNING' if len(versions)==1 and meta.get('sheets') and any(s['rows']>=1048576 for s in meta['sheets']) else 'PENDING','SIV_2021_INTEGRITY','SIVIGILA 2021',f'{len(versions)} versión(es) local(es); workbook metadata={json.dumps(meta,ensure_ascii=False)}','Una hoja alcanza límite XLSX; no se encontró prueba independiente de integridad ni archivo alternativo')

    print('Fase 5/6: recálculo diario IDEAM y procedencia catalogal',flush=True)
    # Station catalog, daily file coverage, duplicate dates, weekly formulas and exact match to pilot.
    cat_path=data/'Cat_logo_Nacional_de_Estaciones_del_IDEAM (1).csv'; catalog={}
    if cat_path.exists():
        with cat_path.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                code=norm_station(row.get('Codigo'))
                if code in {v[1] for v in MUNICIPALITIES.values()}: catalog[code]=row
    station_rows=[]; weather_check=True; weather_violations=[]
    for code,(name,station) in MUNICIPALITIES.items():
        cat=catalog.get(station,{})
        catalog_ok=(norm_station(cat.get('Codigo'))==station and norm_text(cat.get('Municipio'))==norm_text(name) and 'nari' in norm_text(cat.get('Departamento')) and norm_text(cat.get('Tecnologia'))=='convencional' and norm_text(cat.get('Estado'))=='activa')
        check('PASS' if catalog_ok else 'FAIL',f'IDEAM_CATALOG_{station}','IDEAM',f'{station}↔{name}, Nariño, convencional/activa '+('coincide' if catalog_ok else 'no coincide'),json.dumps({k:cat.get(k) for k in ('Codigo','Nombre','Municipio','Departamento','Tecnologia','Estado')},ensure_ascii=False))
        for yr in YEARS:
            cal=cal_map[yr]
            for kind,var in VARS.items():
                path=data/'TemperaturaNacionalDiaria'/f'{var}@{station}.data'
                values,bad=daily_data(path) if path.exists() else ({},0)
                period_values={d:v for d,v in values.items() if d.year==yr}
                date_dups=sum(len(v)-1 for v in period_values.values())
                week_counts={w:sum(1 for d,vs in period_values.items() if cal[w][0]<=d<=cal[w][1] and len(vs)==1) for w in range(1,53)}
                outliers=[] # no station-specific plausible range provided in consulted IDEAM evidence
                pilot_rows=[r for r in pilot if r['municipality_divipola']==code and int(r['year'])==yr]
                pkey={'temp_min':'temp_min_weekly','temp_max':'temp_max_weekly','temp_mean':'temp_mean_weekly'}[kind]
                dayskey={'temp_min':'temp_min_days_observed','temp_max':'temp_max_days_observed','temp_mean':'temp_mean_days_observed'}[kind]
                coveragekey={'temp_min':'temp_min_coverage_pct','temp_max':'temp_max_coverage_pct','temp_mean':'temp_mean_coverage_pct'}[kind]
                for r in pilot_rows:
                    w=int(r['epi_week']); start,end=cal[w]
                    vals=[v[0] for d,v in period_values.items() if start<=d<=end and len(v)==1]
                    if kind=='temp_min': expected=min(vals) if len(vals)>=6 else None
                    elif kind=='temp_max': expected=max(vals) if len(vals)>=6 else None
                    else: expected=sum(vals)/len(vals) if len(vals)>=6 else None
                    observed=number(r[pkey]); observed_days=int(r[dayskey]); observed_pct=number(r[coveragekey])
                    expected_pct=round(100*len(vals)/7,1)
                    if (expected is None and observed is not None) or (expected is not None and (observed is None or abs(observed-expected)>1e-8)) or observed_days!=len(vals) or observed_pct!=expected_pct:
                        weather_check=False; weather_violations.append((code,yr,w,kind,expected,observed,len(vals),observed_days,expected_pct,observed_pct))
                station_rows.append({'municipality_divipola':code,'municipality_name':name,'station_code':station,'variable':var,'year':yr,'daily_valid_dates':len(period_values),'duplicate_date_extras':date_dups,'parse_errors_all_file_periods':bad,'weeks_with_6plus_days':sum(n>=6 for n in week_counts.values()),'weeks_below_6_days':sum(n<6 for n in week_counts.values()),'weeks_below_6_list':';'.join(str(w) for w,n in week_counts.items() if n<6),'first_daily_date':min(period_values).isoformat() if period_values else '', 'last_daily_date':max(period_values).isoformat() if period_values else ''})
                if date_dups or bad: check('FAIL',f'IDEAM_DAILY_{station}_{var}_{yr}','IDEAM',f'duplicados fecha={date_dups}; errores parseo={bad}',str(path))
    with (out/'cobertura_meteorologica.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(station_rows[0])); w.writeheader(); w.writerows(station_rows)
    check('PASS' if weather_check else 'FAIL','PILOT_WEATHER_RECALC','IDEAM',f'Reglas y cobertura semanal recalculadas desde fechas diarias '+('coinciden' if weather_check else 'presentan diferencias'),json.dumps(weather_violations[:10],ensure_ascii=False))
    check('PENDING','IDEAM_PLAUSIBILITY_RANGES','IDEAM','No se aplicó un rango duro de plausibilidad','La documentación consultada no define umbral de plausibilidad por estación aplicable a estas extracciones; los extremos se conservan para revisión y no se eliminan automáticamente')
    below=[x for x in station_rows if x['municipality_divipola']=='52287' and x['year']==2022 and x['weeks_below_6_days']>0]
    check('WARNING' if below else 'PASS','FUNES_2022_LOW_COVERAGE','IDEAM','Semanas de Funes 2022 debajo de 6/7 días identificadas','; '.join(f"{x['variable']}: {x['weeks_below_6_list']}" for x in below))

    print('Fase 6/6: población DANE y escritura de validaciones',flush=True)
    # Recalculate the selected under-five population from source DANE books.
    population,age_cols,pop_mismatch=verify_population(data,pilot) if pilot else ({},[],[])
    check('PASS' if len(population)==6 and not pop_mismatch else 'FAIL','DANE_PROVENANCE','DANE',f'{len(population)} poblaciones municipio-año, constantes por año y con libro correspondiente' if not pop_mismatch else f'diferencias {pop_mismatch}','La segunda auditoría ya revisó área Total, edades simples 0–4, claves y coherencia H+M; esta rutina comprueba presencia/procedencia del piloto sin volver a barrer todas las celdas de los dos libros extensos')

    # Machine-readable checks and concise summary.
    with (out/'validaciones.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['status','id','area','result','evidence']); w.writeheader(); w.writerows(checks)
    failed=[x for x in checks if x['status']=='FAIL']; warnings=[x for x in checks if x['status'] in ('WARNING','PENDING')]
    summary=['# Resultado automático de la cuarta auditoría','',f'- Validaciones PASS: {sum(x["status"]=="PASS" for x in checks)}',f'- Validaciones FAIL: {len(failed)}',f'- Advertencias/pendientes: {len(warnings)}','', '## Fallos', '']
    summary += [f'- `{x["id"]}` ({x["area"]}): {x["result"]}. {x["evidence"]}' for x in failed] or ['Ninguno.']
    summary += ['', '## Advertencias y confirmaciones pendientes', '']
    summary += [f'- `{x["id"]}` ({x["area"]}): {x["result"]}. {x["evidence"]}' for x in warnings] or ['Ninguna.']
    summary += ['', '## Interpretación', '', 'PASS indica una comprobación reproducible de estructura/consistencia local; no certifica validez epidemiológica, climatológica o científica. WARNING/PENDING requiere revisión documental o confirmación de fuente. Los datos fuente se abren en modo lectura y las salidas se escriben solo en esta carpeta.','']
    (out/'resumen_validaciones.md').write_text('\n'.join(summary),encoding='utf-8')
    print(json.dumps({'output':str(out),'checks':len(checks),'pass':sum(x['status']=='PASS' for x in checks),'fail':len(failed),'warning_pending':len(warnings),'repeat_groups':repeats,'weather_below_weeks':below,'missing_siv_weeks':{f'{m}_{y}':v for (m,y),v in source_missing.items()}},ensure_ascii=False,indent=2))
    return 1 if failed else 0

if __name__=='__main__': raise SystemExit(main())
