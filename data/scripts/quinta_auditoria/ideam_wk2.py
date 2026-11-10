import pandas as pd, os
B="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/"
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
cand=pd.read_csv(R+'reports/estaciones_candidatas_ideam.csv',encoding='utf-8-sig')
cal=pd.read_pickle('cal.pkl')
out=[]
for code in cand.codigo_estacion.astype(int):
    for v,folder in [('PTPM_CON_INTER','PrecipitacionNacionalDiaria'),('TSSM_MN_D','TemperaturaNacionalDiaria'),('TSSM_MX_D','TemperaturaNacionalDiaria'),('TSSM_MEDIA_D','TemperaturaNacionalDiaria')]:
        f=f"{B}{folder}/{v}@{code}.data"
        if not os.path.exists(f): continue
        d=pd.read_csv(f,sep='|',dtype={'Fecha':str}); d['date']=pd.to_datetime(d.Fecha.str[:10],errors='coerce'); d['Valor']=pd.to_numeric(d.Valor,errors='coerce')
        d=d.dropna().drop_duplicates('date'); d=d[(d.date>='2012-01-01')&(d.date<='2022-12-31')]
        m=cal.merge(d[['date','Valor']],on='date',how='left'); 
        g=m.groupby(['ey','ew']).Valor.agg(lambda s:int(s.notna().sum())).reset_index(name='dias'); g['codigo_estacion']=code; g['variable']=v
        out.append(g)
pd.concat(out).to_pickle('ideam_wk_days.pkl'); print('ok')
