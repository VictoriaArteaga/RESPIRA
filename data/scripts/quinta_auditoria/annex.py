import pandas as pd, numpy as np
pop=pd.read_csv('pop_u5.csv',dtype={'mpio':str}); pv=pop.pivot(index='mpio',columns='anio',values='t05'); nm=pop.drop_duplicates('mpio').set_index('mpio').municipio
sv=pd.read_csv('siv_mun_cov.csv',dtype={'cod_mun':str}).set_index('cod_mun')
W=pd.read_pickle('w_mun_week.pkl'); wc=W.groupby('mun').size()
J=pd.read_csv('joint_counts.csv',dtype={'mpio':str}).set_index('mpio')
ws=pd.read_csv('ideam_weekly.csv'); mp=pd.read_csv('station_mpio_map.csv',dtype={'mpio':str})
ws=ws.merge(mp[['codigo_estacion','mpio']],on='codigo_estacion')
bt=ws[ws.variable=='TSSM_MEDIA_D'].sort_values('pct_semanas_ge6',ascending=False).drop_duplicates('mpio').set_index('mpio')
bp=ws[ws.variable=='PTPM_CON_INTER'].sort_values('pct_semanas_ge6',ascending=False).drop_duplicates('mpio').set_index('mpio')
lines=['| DIVIPOLA | Municipio | Semanas con fila SIVIGILA (de 574) | Pob. 0–4 2016 | Pob. 0–4 2022 | Mejor estación temperatura (% sem. ≥6/7) | Mejor estación precipitación (% sem. ≥6/7) | Mun-semanas IRA+temperatura |','|---|---|---:|---:|---:|---|---|---:|']
for m in sorted(pv.index):
    n=int(wc.get(m,0))
    t='—'; p='—'; jt=''
    if m in bt.index:
        t=f"{int(bt.loc[m,'codigo_estacion'])} ({bt.loc[m,'pct_semanas_ge6']:.1f}%)"
        if bt.loc[m,'pct_semanas_ge6']<80: t+=' <80%'
    if m in bp.index:
        p=f"{int(bp.loc[m,'codigo_estacion'])} ({bp.loc[m,'pct_semanas_ge6']:.1f}%)"
        if bp.loc[m,'pct_semanas_ge6']<80: p+=' <80%'
    if m in J.index and pd.notna(J.loc[m,'epi_y_temp']): jt=f"{int(J.loc[m,'epi_y_temp'])}"
    lines.append(f"| {m} | {nm[m]} | {n} | {int(pv.loc[m,2016]):,} | {int(pv.loc[m,2022]):,} | {t} | {p} | {jt} |")
open('annex_municipios.md','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print(len(lines)-2); print('\n'.join(lines[:8]))
