import pandas as pd, numpy as np
d=pd.read_pickle('nar_all.pkl'); K=['fy','cod_mun','semana','key']
d['gs']=d.groupby(K).excel_row.transform('size'); r=d[d.gs>1]
rows=[]
for k,x in r.groupby(K):
    nc=x.num_con.tolist()
    vals=x[['iracext_1','iracext_2','iracext_3','totcext_1','totcext_2','totcext_3']].fillna(-1).values.tolist()
    rows.append(dict(fy=k[0],n=len(x),nc_dist=len(set(nc)),consec=(max(nc)-min(nc)+1==len(nc)) if len(set(nc))==len(nc) else False,ident=all(v==vals[0] for v in vals),ira_ident=all(v[:3]==vals[0][:3] for v in vals)))
g=pd.DataFrame(rows)
print('grupos',len(g),'NUM_CON repetido dentro del grupo:',int((g.nc_dist<g.n).sum()),' de ellos filas identicas:',int(((g.nc_dist<g.n)&g.ident).sum()))
print(g[g.nc_dist<g.n].groupby('fy').size().to_dict())
print('NUM_CON consecutivos en el grupo:',int(g.consec.sum()),'/',len(g),round(100*g.consec.mean(),1))
print('grupos con filas identicas Y NUM_CON distinto:',int((g.ident&(g.nc_dist==g.n)).sum()))
print('ira ident:',int(g.ira_ident.sum()))
# mediana municipal 64
sv=pd.read_csv('siv_mun_cov.csv',dtype={'cod_mun':str}); s=sv[sv.cod_mun!='52000']; print(len(s),s.semanas_con_fila_2012_2022.median(),s.pct_semanas_con_fila.median(),(s.pct_semanas_con_fila>=95).sum())
# temp: municipios con archivo temperatura
mp=pd.read_csv('station_mpio_map.csv',dtype={'mpio':str}); w=pd.read_csv('ideam_weekly.csv')
tc=w[w.variable=='TSSM_MEDIA_D'].codigo_estacion.unique(); print('mun con archivo temp:',mp[mp.codigo_estacion.isin(tc)].mpio.nunique())
