import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
W=pd.read_pickle('w_mun_week.pkl'); W=W[W.miss==0].copy()
cal=pd.read_pickle('cal.pkl').groupby(['ey','ew']).size().reset_index()[['ey','ew']]
cal=cal.rename(columns={'ey':'fy','ew':'semana'}); cal['t']=range(len(cal))
W=W.merge(cal,on=['fy','semana'])
J=pd.read_csv('joint_counts.csv',dtype={'mpio':str})
wk=pd.read_pickle('ideam_wk_days.pkl')
def okset(code,vars_,thr=6):
    x=wk[(wk.codigo_estacion==code)&(wk.variable.isin(vars_))].pivot_table(index=['ey','ew'],columns='variable',values='dias')
    return set(x[(x>=thr).all(axis=1)].index)
res=[]
for _,r in J.iterrows():
    m=r.mpio; g=W[W.mun==m].copy()
    g['has_t']=False
    if pd.notna(r.est_temp):
        s=okset(int(r.est_temp),['TSSM_MN_D','TSSM_MX_D','TSSM_MEDIA_D']); g['has_t']=[(a,b) in s for a,b in zip(g.fy,g.semana)]
    # lags: las 4 semanas previas con IRA completa
    ts=set(g.t); g['lag4']=[all((t-k) in ts for k in range(1,5)) for t in g.t]
    g['mpio']=m; res.append(g[['mpio','fy','semana','t','has_t','lag4']])
A=pd.concat(res)
def cnt(df): return df.groupby('fy').size()
print('ESC1 epi (64 mun) por anio:',cnt(A).to_dict(),' total',len(A))
print('ESC1 con lag4:',cnt(A[A.lag4]).to_dict(),' total',int(A.lag4.sum()))
B=A[A.has_t]
print('ESC2 temp (12 mun) por anio:',cnt(B).to_dict(),' total',len(B),' con lag4',int(B.lag4.sum()))
print(' ESC2 con lag4 por anio:',cnt(B[B.lag4]).to_dict())
for lab,sel in (('train 2012-2018',lambda x:x.fy<=2018),('val 2019',lambda x:x.fy==2019),('2020-2021',lambda x:x.fy.isin([2020,2021])),('test 2022',lambda x:x.fy==2022)):
    print(lab,'ESC1',int(sel(A[A.lag4]).sum()),'ESC2',int(sel(B[B.lag4]).sum()))
# municipio-semana con ambos temperatura y consistencia de aldana (excluir)
C=B[B.mpio!='52022']; print('ESC2 sin Aldana:',len(C),'mun',C.mpio.nunique())
# anual: proporcion de mun-semanas con IRA = 0
Wf=pd.read_pickle('w_mun_week.pkl'); Wf=Wf[Wf.miss==0]
print('ceros 12 mun temp:',round((Wf[Wf.mun.isin(J[J.est_temp.notna()].mpio)].ira==0).mean(),3),' ceros 64:',round((Wf.ira==0).mean(),3))
mm=Wf[Wf.mun.isin(J[J.est_temp.notna()].mpio)&Wf.fy.isin([2019,2022])].groupby('mun').ira.median()
print(mm.round(1).to_dict())
