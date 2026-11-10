import pandas as pd, numpy as np, datetime as dt, os, sys
B="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/"
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
cand=pd.read_csv(R+'reports/estaciones_candidatas_ideam.csv',encoding='utf-8-sig')
def se1_start(y):
    j=dt.date(y,1,4)               # regla MMWR: SE1 contiene el 4 de enero (dom-sab)
    return j-dt.timedelta(days=(j.weekday()+1)%7)
starts={y:se1_start(y) for y in range(2011,2024)}
def epi(d):
    d=d.date() if hasattr(d,'date') else d
    y=d.year
    for yy in (y+1,y,y-1):
        if d>=starts[yy]: 
            return yy,(d-starts[yy]).days//7+1
rng=pd.date_range('2012-01-01','2022-12-31')
cal=pd.DataFrame({'date':rng}); ey=[epi(d) for d in rng]; cal['ey']=[a for a,b in ey]; cal['ew']=[b for a,b in ey]
cal=cal[(cal.ey>=2012)&(cal.ey<=2022)]
# semanas epi completas 2012-2022 (todas las del año epi) -> referencia
allweeks=cal.groupby(['ey','ew']).size()
full=allweeks[allweeks==7].index
print('semanas epi 2012-2022 totalmente dentro del rango:',len(full))
cal.to_pickle('cal.pkl')
rows=[];cons=[]
VARS=[('PTPM_CON_INTER','PrecipitacionNacionalDiaria'),('TSSM_MN_D','TemperaturaNacionalDiaria'),('TSSM_MX_D','TemperaturaNacionalDiaria'),('TSSM_MEDIA_D','TemperaturaNacionalDiaria')]
daily={}
for _,s in cand.iterrows():
    code=int(s.codigo_estacion)
    for v,folder in VARS:
        f=f"{B}{folder}/{v}@{code}.data"
        if not os.path.exists(f): continue
        d=pd.read_csv(f,sep='|',dtype={'Fecha':str})
        d['date']=pd.to_datetime(d.Fecha.str[:10],errors='coerce'); d['Valor']=pd.to_numeric(d.Valor,errors='coerce')
        nraw=len(d); dups=int(d.date.duplicated().sum()); nbad=int(d.date.isna().sum()+d.Valor.isna().sum())
        d=d.dropna().drop_duplicates('date')
        w=d[(d.date>='2012-01-01')&(d.date<='2022-12-31')]
        m=cal.merge(w[['date','Valor']],on='date',how='left')
        m['ok']=m.Valor.notna()
        g=m.groupby(['ey','ew']).ok.sum().reindex(full).fillna(0)
        ge6=(g>=6); eq7=(g>=7)
        # racha maxima de semanas consecutivas sin >=6 dias
        run=best=0
        for x in ge6.values:
            run=0 if x else run+1; best=max(best,run)
        peryear=ge6.groupby(level=0).sum()
        daily[(code,v)]=w.set_index('date').Valor
        rows.append(dict(codigo_estacion=code,variable=v,fecha_min_archivo=str(d.date.min().date()),fecha_max_archivo=str(d.date.max().date()),
            dias_validos_2012_2022=int(m.ok.sum()),dias_calendario=len(m),pct_dias=round(100*m.ok.sum()/len(m),2),
            semanas_epi_ref=len(full),semanas_ge6de7=int(ge6.sum()),semanas_7de7=int(eq7.sum()),pct_semanas_ge6=round(100*ge6.mean(),2),pct_semanas_7de7=round(100*eq7.mean(),2),
            max_racha_semanas_sin_ge6=best,anios_con_ge80pct_semanas=int(((peryear/ge6.groupby(level=0).size())>=0.8).sum()),
            filas_archivo=nraw,fechas_duplicadas=dups,valores_no_numericos_o_fecha_invalida=nbad,
            vmin=float(w.Valor.min()) if len(w) else None,vmax=float(w.Valor.max()) if len(w) else None,
            n_gt135=int((w.Valor>135).sum()) if v.startswith('PTPM') else None,
            n_neg=int((w.Valor<0).sum()),**{f'wk_ge6_{y}':int(peryear.get(y,0)) for y in range(2012,2023)}))
res=pd.DataFrame(rows); res.to_csv('ideam_weekly.csv',index=False)
# consistencia fisica tmin<=tmedia<=tmax
for code in cand.codigo_estacion.astype(int):
    if all((code,v) in daily for v in ('TSSM_MN_D','TSSM_MX_D','TSSM_MEDIA_D')):
        t=pd.concat([daily[(code,'TSSM_MN_D')],daily[(code,'TSSM_MX_D')],daily[(code,'TSSM_MEDIA_D')]],axis=1,keys=['mn','mx','me']).dropna()
        cons.append(dict(codigo_estacion=code,dias_con_3vars=len(t),mn_gt_mx=int((t.mn>t.mx).sum()),mean_lt_mn=int((t.me<t.mn-1e-9).sum()),mean_gt_mx=int((t.me>t.mx+1e-9).sum())))
pd.DataFrame(cons).to_csv('ideam_consist.csv',index=False)
print(len(res),'series',len(cons),'estaciones consistencia')
