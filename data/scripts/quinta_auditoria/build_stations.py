import pandas as pd, numpy as np
R="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
OUT=R+"reports/quinta_auditoria/"
c=pd.read_csv(R+'reports/estaciones_candidatas_ideam.csv',encoding='utf-8-sig')
mp=pd.read_csv('station_mpio_map.csv',dtype={'mpio':str}).set_index('codigo_estacion').mpio
w=pd.read_csv('ideam_weekly.csv'); cons=pd.read_csv('ideam_consist2.csv').set_index('codigo_estacion')
short={'PTPM_CON_INTER':'prec','TSSM_MN_D':'tmin','TSSM_MX_D':'tmax','TSSM_MEDIA_D':'tmedia'}
rows=[]
for _,s in c.iterrows():
    code=int(s.codigo_estacion)
    r=dict(codigo_estacion=code,nombre_estacion=s.nombre_estacion.split(' [')[0].strip(),municipio_catalogo=s.municipio,divipola_municipio_por_nombre=mp.get(code),
           departamento=s.departamento,latitud=s.latitud,longitud=s.longitud,altitud_m=s.altitud,categoria=s.categoria,tecnologia=s.tecnologia,estado_catalogo=s.estado_catalogo,
           estado_auditoria_previa=s.estado,en_piloto=('SI' if code in (52045020,52055200,52055060) else 'NO'))
    best=[]
    for v,k in short.items():
        x=w[(w.codigo_estacion==code)&(w.variable==v)]
        if len(x)==0:
            for f in ('dias_validos','pct_dias','pct_sem_ge6de7','pct_sem_7de7','max_racha_sem_sin_ge6','anios_ge80pct_sem'): r[f'{k}_{f}']=np.nan
            r[f'{k}_archivo']='NO_EXISTE'; continue
        x=x.iloc[0]
        r[f'{k}_archivo']=f"{x.fecha_min_archivo}..{x.fecha_max_archivo}"
        r[f'{k}_dias_validos']=x.dias_validos_2012_2022; r[f'{k}_pct_dias']=x.pct_dias; r[f'{k}_pct_sem_ge6de7']=x.pct_semanas_ge6; r[f'{k}_pct_sem_7de7']=x.pct_semanas_7de7
        r[f'{k}_max_racha_sem_sin_ge6']=x.max_racha_semanas_sin_ge6; r[f'{k}_anios_ge80pct_sem']=x.anios_con_ge80pct_semanas
        if k=='prec': r['prec_n_gt135mm']=x.n_gt135
    t=[r.get(f'{k}_pct_sem_ge6de7') for k in ('tmin','tmax','tmedia')]
    tmin_cov=np.nanmin(t) if not all(pd.isna(t)) else np.nan
    def cls(v): 
        return 'SIN_ARCHIVO' if pd.isna(v) else ('ALTA(>=95)' if v>=95 else 'MEDIA(80-95)' if v>=80 else 'BAJA(<80)')
    r['clase_cobertura_temperatura']=cls(tmin_cov); r['clase_cobertura_precipitacion']=cls(r.get('prec_pct_sem_ge6de7'))
    if code in cons.index:
        q=cons.loc[code]; r.update(temp_dias_con_3vars=int(q.dias_comunes) if pd.notna(q.dias_comunes) else q.dias_con_3vars, temp_dias_mn_igual_mx=q.mn_igual_mx, temp_dias_media_gt_max=q.mean_gt_mx, temp_dias_media_lt_min=q.mean_lt_mn, temp_dias_mn_gt_mx=q.mn_gt_mx)
    obs=[]
    if code==52055230: obs.append('ANOMALIA: TSSM_MN_D y TSSM_MX_D son identicas en 4016/4016 dias y TSSM_MEDIA_D > TSSM_MX_D en 4016/4016 dias; NO usar min/max de esta estacion hasta aclarar con IDEAM (cobertura alta no implica calidad).')
    if code==52045020: obs.append('Estacion Aeropuerto Antonio Narino (aeropuerto de Pasto) catalogada en Chachagui; representatividad para el casco urbano de Chachagui no evaluada.')
    if s.estado_catalogo!='Activa': obs.append(f'Estado en catalogo: {s.estado_catalogo}.')
    if r['clase_cobertura_temperatura'] in ('ALTA(>=95)','MEDIA(80-95)') and not obs: obs.append('Cobertura semanal temperatura suficiente para evaluacion; representatividad municipal pendiente (D-03).')
    if pd.notna(r.get('prec_n_gt135mm')) and r['prec_n_gt135mm']>0: obs.append(f"{int(r['prec_n_gt135mm'])} dias >135 mm en 2012-2022 (alerta de revision IDEAM GDI-M005, no eliminar).")
    r['observaciones']=' | '.join(obs)
    rows.append(r)
df=pd.DataFrame(rows)
df.to_csv(OUT+'EVALUACION_ESTACIONES_IDEAM.csv',index=False,encoding='utf-8-sig')
print(df.shape); print(df.clase_cobertura_temperatura.value_counts().to_dict()); print(df.clase_cobertura_precipitacion.value_counts().to_dict())
print(df.groupby('estado_catalogo').size().to_dict())
print('estaciones precip ALTA por estado:',df[df.clase_cobertura_precipitacion.str.startswith('ALTA')].estado_catalogo.value_counts().to_dict())
print('municipios con alguna estacion:',df.divipola_municipio_por_nombre.nunique())
