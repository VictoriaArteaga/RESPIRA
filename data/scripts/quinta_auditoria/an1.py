import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
fr=[]
for y in range(2012,2023):
    d=pd.read_csv(f'nar_{y}.csv',dtype=str); d['fy']=y; fr.append(d)
d=pd.concat(fr,ignore_index=True)
for c in ['semana','ano','num_con','iracext_1','iracext_2','iracext_3','tot_iraext','totcext_1','totcext_2','totcext_3','tot_exturg','ajuste','excel_row']:
    d[c]=pd.to_numeric(d[c],errors='coerce')
d['key']=d.cod_pre.str.lstrip('0')+'|'+d.cod_sub.fillna('').str.lstrip('0')
d['ira04']=d[['iracext_1','iracext_2','iracext_3']].sum(axis=1,min_count=1)
d['ira04_all3']=d[['iracext_1','iracext_2','iracext_3']].notna().all(axis=1)
d['tot04']=d[['totcext_1','totcext_2','totcext_3']].sum(axis=1,min_count=1)
d.to_pickle('nar_all.pkl')
rows=[]
for y,g in d.groupby('fy'):
    mw=g.groupby(['cod_mun','ano','semana']).size()
    grp=g.groupby(['cod_mun','ano','semana','key']).size()
    rows.append(dict(anio=y,filas_nar=len(g),municipios=g.cod_mun.nunique(),upgd=g.cod_pre.str.lstrip('0').nunique(),ano_distinto_al_archivo=int((g.ano!=y).sum()),max_semana=int(g.semana.max()),filas_sem53=int((g.semana==53).sum()),
      ajuste_no_nulo_gt0=int((g.ajuste>0).sum()),ajuste_vals=str(sorted(g.ajuste.dropna().astype(int).unique().tolist())),
      iracext_alguna_nula=int((~g.ira04_all3).sum()),num_con_nulo=int(g.num_con.isna().sum()),
      filas_por_mun_sem_media=round(mw.mean(),2),filas_por_mun_sem_max=int(mw.max()),
      grupos_prestador_semana_repetidos=int((grp>1).sum()),filas_en_grupos_repetidos=int(grp[grp>1].sum()),
      ira04_total=int(g.ira04.sum()),tot04_total=int(g.tot04.sum())))
r=pd.DataFrame(rows); print(r.T)
r.to_csv('siv_year_summary.csv',index=False)
