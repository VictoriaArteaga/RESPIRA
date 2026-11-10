import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
d=pd.read_pickle('nar_all.pkl'); d['i']=d.ira04.fillna(0)
K=['fy','cod_mun','semana','key']
def agg(rule):
    s=d.sort_values(['num_con','excel_row'])
    if rule=='suma': t=d
    elif rule=='ultimo (mayor NUM_CON)': t=s.groupby(K).tail(1)
    elif rule=='primero (menor NUM_CON)': t=s.groupby(K).head(1)
    elif rule=='max valor': t=d.sort_values('i').groupby(K).tail(1)
    return t.groupby('fy').i.sum()
S=pd.DataFrame({r_:agg(r_) for r_ in ['suma','ultimo (mayor NUM_CON)','primero (menor NUM_CON)','max valor']})
S['suma/ultimo']=(S['suma']/S['ultimo (mayor NUM_CON)']).round(3); S['suma/primero']=(S['suma']/S['primero (menor NUM_CON)']).round(3)
print(S); S.to_csv('consol_sens.csv')
# efecto en el nivel municipio-semana: % de celdas municipio-semana afectadas por grupos repetidos
d['gs']=d.groupby(K).excel_row.transform('size')
ms=d.groupby(['fy','cod_mun','semana']).agg(rep=('gs',lambda s:(s>1).any()),n=('gs','size')).reset_index()
print(ms.groupby('fy').rep.agg(['sum','size']).assign(pct=lambda t:(100*t['sum']/t['size']).round(1)))
# cobertura municipio-semana por anio: semanas con >=1 fila
wk={y:(53 if y in(2014,2020) else 52) for y in range(2012,2023)}
cov=d.groupby(['fy','cod_mun']).semana.nunique().unstack(0)
print((cov.notna().sum()))
tot=sum(wk.values()); print('semanas totales',tot)
mcov=cov.fillna(0).sum(axis=1); print(mcov.describe())
names=d.groupby('cod_mun').nmun_notif.agg(lambda s:s.mode().iloc[0])
out=pd.DataFrame({'municipio_sivigila':names,'semanas_con_fila_2012_2022':mcov.astype(int),'pct_semanas_con_fila':(100*mcov/tot).round(1)})
for y in range(2012,2023): out[f'sem_{y}']=cov[y].fillna(0).astype(int)
out.to_csv('siv_mun_cov.csv'); print(out.sort_values('pct_semanas_con_fila').head(15)); print((out.pct_semanas_con_fila>=95).sum(),(out.pct_semanas_con_fila>=80).sum(),len(out))
# nulos en iracext en municipios piloto
print(d[(d.cod_mun.isin(['52240','52287','52678']))&(~d.ira04_all3)][['fy','cod_mun','semana','iracext_1','iracext_2','iracext_3']])
print(d[~d.ira04_all3].groupby(['fy']).agg(n=('semana','size'),mun=('cod_mun','nunique')))
