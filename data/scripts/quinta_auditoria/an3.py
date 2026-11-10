import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
d=pd.read_pickle('nar_all.pkl')
# 1) NUM_CON como contador por UPGD: dif entre semanas consecutivas
res=[]
for y,g in d.groupby('fy'):
    g=g.sort_values(['key','semana','excel_row'])
    # un registro por key-semana: tomar el primero y el ultimo
    first=g.groupby(['key','semana']).num_con.min().reset_index()
    last=g.groupby(['key','semana']).num_con.max().reset_index()
    f=first.sort_values(['key','semana']); f['d']=f.groupby('key').num_con.diff(); f['ds']=f.groupby('key').semana.diff()
    f1=f[f.ds==1]
    res.append(dict(fy=y,pares_semanas_consecutivas=len(f1),dif_eq1=int((f1.d==1).sum()),dif_gt1=int((f1.d>1).sum()),dif_le0=int((f1.d<=0).sum()),pct_eq1=round(100*(f1.d==1).mean(),1),mediana_dif=float(f1.d.median())))
print(pd.DataFrame(res))
# 2) en grupos repetidos: continuidad del contador (fila siguiente semana = ultima+1 ?)
rows=[]
for (y,m,s,k),x in d[d.groupby(['fy','cod_mun','semana','key']).excel_row.transform('size')>1].groupby(['fy','cod_mun','semana','key']):
    x=x.sort_values('num_con'); rows.append((y,m,s,k,x.num_con.min(),x.num_con.max(),len(x)))
r=pd.DataFrame(rows,columns=['fy','mun','sem','key','nmin','nmax','n'])
allk=d.groupby(['fy','key','semana']).num_con.agg(['min','max']).reset_index()
mm=r.merge(allk.rename(columns={'min':'pmin','max':'pmax','semana':'sem_prev'}).assign(sem=lambda t:t.sem_prev+1)[['fy','key','sem','pmin','pmax']],on=['fy','key','sem'],how='left')
mp=r.merge(allk.assign(sem=lambda t:t.semana+1)[['fy','key','sem','min','max']].rename(columns={'min':'qmin','max':'qmax'}),on=['fy','key','sem'],how='left')
# semana previa vs grupo
prev=r.merge(allk.assign(sem=lambda t:t.semana+1).rename(columns={'max':'prev_max'})[['fy','key','sem','prev_max']],on=['fy','key','sem'],how='left')
prev['gap']=prev.nmin-prev.prev_max
nxt=r.merge(allk.assign(sem=lambda t:t.semana-1).rename(columns={'min':'next_min'})[['fy','key','sem','next_min']],on=['fy','key','sem'],how='left')
nxt['gap']=nxt.next_min-nxt.nmax
print('prev->grupo gap (nmin - prev_max):',prev.gap.value_counts(dropna=False).head(6).to_dict())
print('grupo->next gap (next_min - nmax):',nxt.gap.value_counts(dropna=False).head(6).to_dict())
print('n_en_grupo vs span',(r.nmax-r.nmin+1==r.n).mean())
# 3) sensibilidad de reglas de consolidacion (solo analisis)
d['rk']=d.groupby(['fy','cod_mun','semana','key']).num_con.rank(method='first',ascending=True)
def agg(rule):
    if rule=='suma': t=d
    elif rule=='ultimo': t=d.sort_values('num_con').groupby(['fy','cod_mun','semana','key']).tail(1)
    elif rule=='primero': t=d.sort_values('num_con').groupby(['fy','cod_mun','semana','key']).head(1)
    elif rule=='max': t=d.loc[d.groupby(['fy','cod_mun','semana','key']).ira04.idxmax().dropna()]
    return t.groupby('fy').ira04.sum()
S=pd.DataFrame({r_:agg(r_) for r_ in ['suma','ultimo','primero','max']})
S['suma/ultimo']=(S.suma/S.ultimo).round(3); S['suma/max']=(S.suma/S.max).round(3)
print(S)
S.to_csv('consol_sens.csv')
