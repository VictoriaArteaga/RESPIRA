import pandas as pd, numpy as np, unicodedata, re
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
def nz(s): 
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().upper()
    s=re.sub(r'\(.*?\)','',s); return re.sub(r'[^A-Z ]','',s).strip()
pop=pd.read_csv('pop_u5.csv',dtype={'mpio':str})
dn=pop.drop_duplicates('mpio').set_index('mpio').municipio
dnorm={nz(v):k for k,v in dn.items()}
print(len(dnorm))
c=pd.read_csv(R+'reports/estaciones_candidatas_ideam.csv',encoding='utf-8-sig')
mm={}
for m in c.municipio.unique():
    k=nz(m); mm[m]=dnorm.get(k)
print({m:v for m,v in mm.items() if v is None})
# salto 2017->2018
pv=pop.pivot(index='mpio',columns='anio',values='t05')
j=(pv[2018]/pv[2017]-1)*100; print(j.describe().round(2)); print('mpios con salto>5%:',(j>5).sum(),' <-5%:',(j<-5).sum())
y=(pv[2017]/pv[2016]-1)*100; print('var 2016-17 mediana',round(y.median(),2),' 2018-19',round(((pv[2019]/pv[2018]-1)*100).median(),2))
# estaciones por municipio
w=pd.read_csv('ideam_weekly.csv').merge(c[['codigo_estacion','municipio']],on='codigo_estacion')
w['mpio']=w.municipio.map(mm)
t=w[w.variable=='TSSM_MEDIA_D'].groupby('mpio').pct_semanas_ge6.max()
pr=w[w.variable=='PTPM_CON_INTER'].groupby('mpio').pct_semanas_ge6.max()
print('mpios con alguna estacion temp (catalogo candidatas):',t.size,' >=80% semanas:',(t>=80).sum(),' >=90:',(t>=90).sum())
print('mpios con alguna estacion prec:',pr.size,' >=80% semanas:',(pr>=80).sum(),' >=90:',(pr>=90).sum())
sv=pd.read_csv('siv_mun_cov.csv',dtype={'cod_mun':str}).set_index('cod_mun')
tab=pd.DataFrame({'municipio':dn}).join(sv[['pct_semanas_con_fila']]).join(t.rename('temp_best_pct_sem')).join(pr.rename('prec_best_pct_sem'))
tab=tab.join(pv[[2012,2016,2018,2022]].rename(columns=lambda x:f'pob04_{x}'))
tab['epi_ok95']=tab.pct_semanas_con_fila>=95
tab.to_csv('mun_master.csv')
print(tab[(tab.temp_best_pct_sem>=80)].to_string())
print('temp>=80 & epi>=95:',((tab.temp_best_pct_sem>=80)&(tab.pct_semanas_con_fila>=95)).sum(), ' prec>=80 & epi>=95:',((tab.prec_best_pct_sem>=80)&(tab.pct_semanas_con_fila>=95)).sum(), ' prec>=80 & epi>=80:',((tab.prec_best_pct_sem>=80)&(tab.pct_semanas_con_fila>=80)).sum())
print(tab.pct_semanas_con_fila.describe())
# poblacion pequeña
print((pv[2022]<500).sum(),'municipios con pob0-4 <500 en 2022;',(pv[2022]<1000).sum(),'<1000')
