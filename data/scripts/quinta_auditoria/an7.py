import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
d=pd.read_pickle('nar_all.pkl')
d['mun']=d.cod_mun.replace({'52000':'52001'})   # solo para conteo exploratorio; 1 fila 2012 con codigo 52000
w=d.groupby(['mun','fy','semana']).agg(ira=('ira04','sum'),tot=('tot04','sum'),filas=('excel_row','size'),miss=('ira04_all3',lambda s:(~s).sum())).reset_index()
w.to_pickle('w_mun_week.pkl')
print('municipio-semanas con fila:',len(w), 'de', 64*574)
print(w.groupby('fy').agg(mw=('ira','size'),ira=('ira','sum'),med=('ira','median'),cero=('ira',lambda s:(s==0).mean())).round(3))
s=w[w.fy.isin([2012,2013,2014,2015,2016,2017,2018,2019,2022])]
g=s.groupby('mun').ira.agg(['median','mean',lambda x:(x==0).mean()]); g.columns=['med','mean','p0']
print(g.describe().round(2)); print('mun con mediana semanal <3:',(g['med']<3).sum(),' <10:',(g['med']<10).sum(),' >=10:',(g['med']>=10).sum())
tot=w.groupby(['fy','semana']).ira.sum().reset_index()
print(tot.groupby('fy').ira.agg(['min','median','max']))
# proporcion IRA/consultas totales
w['prop']=w.ira/w.tot.replace(0,np.nan)
print(w.groupby('fy').prop.median().round(3))
# 2020-2021 comparacion
print(w[w.fy.isin([2019,2020,2021,2022])].groupby('fy').agg(ira=('ira','sum'),tot=('tot','sum')).assign(p=lambda t:(t.ira/t.tot).round(3)))
