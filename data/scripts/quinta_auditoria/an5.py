import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
d=pd.read_pickle('nar_all.pkl')
p=pd.read_csv(R+'data/processed/pilot/piloto_respira_2016_2022.csv',encoding='utf-8-sig')
# recomputo SIVIGILA
x=d[d.cod_mun.isin(['52240','52287','52678'])&d.fy.isin([2016,2022])]
a=x.groupby(['cod_mun','fy','semana']).agg(ira=('ira04','sum'),rows=('excel_row','size')).reset_index()
a['municipality_divipola']=a.cod_mun.astype(int); a=a.rename(columns={'fy':'year','semana':'epi_week'})
m=p.merge(a,on=['municipality_divipola','year','epi_week'],how='left')
m['ira']=m.ira.where(m.rows.notna())
cmp=((m.ira==m.ira_under5_reported_consultations)|(m.ira.isna()&m.ira_under5_reported_consultations.isna()))
print('semanas coinciden IRA:',int(cmp.sum()),'/312; filas coinciden:',int(((m.rows.fillna(0))==m.sivigila_source_rows).sum()))
print(m[~cmp][['municipality_divipola','year','epi_week','ira','ira_under5_reported_consultations']])
# poblacion
def load(t):
    cols=['excel_row','dp','mpio','municipio','anio','area']+[f'{s}_{a}' for s in ('hombres','mujeres','total') for a in range(5)]+['total_general','dp_name']
    z=pd.read_csv(f'dane_{t}.csv',dtype={'mpio':str},encoding='utf-8',header=None if t=='a' else 0,names=cols if t=='a' else None)
    return z
a_=load('a'); b_=load('b')
print(a_.shape,b_.shape,a_.area.unique(),b_.area.unique()); print(a_.head(2).T.head(20)); print(b_.head(2).T.head(20))
for nm,z in (('a',a_),('b',b_)):
    z['t05']=z[[f'total_{i}' for i in range(5)]].sum(axis=1,min_count=5)
    z['hm05']=z[[f'hombres_{i}' for i in range(5)]+[f'mujeres_{i}' for i in range(5)]].sum(axis=1,min_count=10)
    zt=z[z.area=='Total']
    print(nm,'filas Total',len(zt),'mpios',zt.mpio.nunique(),'anios',sorted(zt.anio.unique())[:3],sorted(zt.anio.unique())[-3:],'nulos t05',int(zt.t05.isna().sum()),'t05!=hm05',int((zt.t05!=zt.hm05).sum()),'dups',int(zt.duplicated(['mpio','anio']).sum()))
    z.to_pickle(f'dane_{nm}.pkl')
pop=pd.concat([a_[a_.area=='Total'],b_[b_.area=='Total']]); pop=pop[(pop.anio>=2012)&(pop.anio<=2022)]
pop['mpio']=pop.mpio.astype(str); 
pop['t05']=pop[[f'total_{i}' for i in range(5)]].sum(axis=1)
pop[['mpio','municipio','anio','t05']].to_csv('pop_u5.csv',index=False)
print(len(pop),pop.mpio.nunique(),pop.groupby('anio').size().to_dict())
pv=pop.pivot(index='mpio',columns='anio',values='t05'); print(pv.loc[['52240','52287','52678']])
print(pv.describe().T[['min','50%','max']].T)
print('menores de 200:', (pv<200).sum().sum(), 'menores de 500:',(pv<500).sum().sum())
# muni de Nariño en DANE vs en SIVIGILA
sv=pd.read_csv('siv_mun_cov.csv',dtype={'cod_mun':str}); print(set(sv.cod_mun)-set(pv.index),set(pv.index)-set(sv.cod_mun))
