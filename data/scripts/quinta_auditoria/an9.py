import pandas as pd, numpy as np, datetime as dt
B="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/TemperaturaNacionalDiaria/"
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
p=pd.read_csv(R+'data/processed/pilot/piloto_respira_2016_2022.csv',encoding='utf-8-sig')
v2=pd.read_csv(R+'reports/cuarta_auditoria/piloto_respira_2016_2022_auditado_v2.csv',encoding='utf-8-sig')
print(p.loc[p.quality_notes!=v2.quality_notes,['municipality_divipola','year','epi_week','quality_notes']].assign(v2=v2.loc[p.quality_notes!=v2.quality_notes,'quality_notes']).to_string())
res={}
for v,col,fn in (('TSSM_MN_D','temp_min_weekly','min'),('TSSM_MX_D','temp_max_weekly','max'),('TSSM_MEDIA_D','temp_mean_weekly','mean')):
    ok=tot=bad=0; maxdiff=0
    for code,g in p.groupby('ideam_station_code'):
        d=pd.read_csv(f'{B}{v}@{code}.data',sep='|'); d['date']=pd.to_datetime(d.Fecha.str[:10]); d=d.drop_duplicates('date').set_index('date').Valor
        for _,r in g.iterrows():
            w=d[(d.index>=r.epi_week_start)&(d.index<=r.epi_week_end)]
            n=len(w); val=getattr(w,fn)() if n>=6 else np.nan
            exp=r[col]; tot+=1
            same=(np.isnan(val) and pd.isna(exp)) or (not np.isnan(val) and not pd.isna(exp) and abs(val-exp)<1e-4)
            ok+=same
            if n!=r[col.replace('weekly','days_observed')]: bad+=1
            if same and not pd.isna(exp): maxdiff=max(maxdiff,abs(val-exp))
    res[v]=(ok,tot,bad,maxdiff)
print(res)
# calendario: regla ingenua vs MMWR
def mm(y):
    j=dt.date(y,1,4); return j-dt.timedelta(days=(j.weekday()+1)%7)
def naive(y):
    j=dt.date(y,1,1); return j+dt.timedelta(days=(6-j.weekday())%7)
rows=[]
for y in range(2012,2024):
    a=mm(y); b=naive(y); n=(mm(y+1)-a).days//7
    rows.append((y,str(a),str(b),(b-a).days,n))
print(pd.DataFrame(rows,columns=['anio','SE1_inicio_regla_Jan4','SE1_inicio_primer_domingo','dif_dias','semanas_en_anio']).to_string())
