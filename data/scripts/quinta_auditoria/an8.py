import pandas as pd, numpy as np, unicodedata, re
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
def nz(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().upper(); s=re.sub(r'\(.*?\)','',s); return re.sub(r'[^A-Z ]','',s).strip()
pop=pd.read_csv('pop_u5.csv',dtype={'mpio':str}); dn=pop.drop_duplicates('mpio').set_index('mpio').municipio
print({k:v for k,v in dn.items() if k in ('52835','52258','52699')})
dnorm={nz(v):k for k,v in dn.items()}
over={'TUMACO':'52835','EL TABLON':'52258','SANTA CRUZ':'52699'}
c=pd.read_csv(R+'reports/estaciones_candidatas_ideam.csv',encoding='utf-8-sig')
c['mpio']=c.municipio.map(lambda m: dnorm.get(nz(m)) or over.get(nz(m)))
print('sin mapear:',c[c.mpio.isna()].municipio.unique())
c[['codigo_estacion','municipio','mpio']].to_csv('station_mpio_map.csv',index=False)
wk=pd.read_pickle('ideam_wk_days.pkl')
W=pd.read_pickle('w_mun_week.pkl')
ws=pd.read_csv('ideam_weekly.csv')
# estacion por municipio: la de mayor % semanas >=6 para TSSM_MEDIA_D; precip idem
def best(var):
    x=ws[ws.variable==var].merge(c[['codigo_estacion','mpio']],on='codigo_estacion')
    return x.sort_values('pct_semanas_ge6',ascending=False).drop_duplicates('mpio').set_index('mpio')
bt=best('TSSM_MEDIA_D'); bp=best('PTPM_CON_INTER')
def okweeks(code,vars_,thr):
    x=wk[(wk.codigo_estacion==code)&(wk.variable.isin(vars_))]
    p=x.pivot_table(index=['ey','ew'],columns='variable',values='dias')
    if p.shape[1]<len(vars_): return set()
    return set(p[(p>=thr).all(axis=1)].index)
rows=[]
for m in W.mun.unique():
    base=W[(W.mun==m)&(W.miss==0)]
    es=set(zip(base.fy,base.semana))
    r=dict(mpio=m,epi_semanas=len(es))
    if m in bt.index and bt.loc[m,'pct_semanas_ge6']>=80:
        t=okweeks(int(bt.loc[m,'codigo_estacion']),['TSSM_MN_D','TSSM_MX_D','TSSM_MEDIA_D'],6)
        r.update(est_temp=int(bt.loc[m,'codigo_estacion']),temp_semanas=len(t),epi_y_temp=len(es&t))
        e2=set((y,s) for y,s in es if y not in(2020,2021)); r['epi_y_temp_sin2020_21']=len(e2&t)
    if m in bp.index and bp.loc[m,'pct_semanas_ge6']>=80:
        p=okweeks(int(bp.loc[m,'codigo_estacion']),['PTPM_CON_INTER'],6)
        r.update(est_prec=int(bp.loc[m,'codigo_estacion']),prec_semanas=len(p),epi_y_prec=len(es&p))
        if 'est_temp' in r: 
            r['epi_temp_prec']=len(es&t&p)
    rows.append(r)
J=pd.DataFrame(rows); J.to_csv('joint_counts.csv',index=False)
print('Mun con epi:',len(J),' epi total:',J.epi_semanas.sum())
print('Escenario temp: mun',J.epi_y_temp.notna().sum(),' obs',int(J.epi_y_temp.sum()),' sin2020-21',int(J.epi_y_temp_sin2020_21.sum()))
print('Escenario prec: mun',J.epi_y_prec.notna().sum(),' obs',int(J.epi_y_prec.sum()))
print('Esc temp+prec: mun',J.epi_temp_prec.notna().sum(),' obs',int(J.epi_temp_prec.sum()))
print(J[J.est_temp.notna()].to_string())
