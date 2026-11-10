import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_columns',60,'display.max_rows',500)
d=pd.read_pickle('nar_all.pkl')
g=d.groupby(['fy','cod_mun','semana','key'])
d['gsize']=g.excel_row.transform('size')
rep=d[d.gsize>1].copy()
print('filas en grupos repetidos',len(rep),'grupos',rep.groupby(['fy','cod_mun','semana','key']).ngroups)
# caracterizar cada grupo
out=[]
for k,x in rep.groupby(['fy','cod_mun','semana','key']):
    x=x.sort_values('excel_row')
    vals=x[['iracext_1','iracext_2','iracext_3','totcext_1','totcext_2','totcext_3']].fillna(-1).values.tolist()
    identical=all(v==vals[0] for v in vals)
    ira_identical=all(v[:3]==vals[0][:3] for v in vals)
    nc=x.num_con.tolist()
    out.append(dict(fy=k[0],mun=k[1],sem=k[2],n=len(x),num_con_distintos=len(set(nc)),num_con_crec_con_fila=nc==sorted(nc),
        ajustes='/'.join(str(int(a)) if pd.notna(a) else 'NA' for a in x.ajuste),
        fec_not_iguales=x.fec_not.nunique()==1,fila_identica_valores=identical,ira_identica=ira_identical,
        ira_sum=x.ira04.sum(),ira_max=x.ira04.max(),ira_ultima=x.ira04.iloc[-1],ira_primera=x.ira04.iloc[0],
        tot_ultima_ge_primera=(x.tot04.iloc[-1]>=x.tot04.iloc[0]),
        ultima_ge_primera=(x.ira04.iloc[-1]>=x.ira04.iloc[0])))
o=pd.DataFrame(out); o.to_csv('rep_groups.csv',index=False)
print(o.groupby('fy').agg(grupos=('n','size'),n2=('n',lambda s:(s==2).sum()),n3mas=('n',lambda s:(s>2).sum()),num_con_dist=('num_con_distintos',lambda s:(s>1).sum()),
    ident=('fila_identica_valores','sum'),ira_ident=('ira_identica','sum'),mismo_fecnot=('fec_not_iguales','sum'),conaj7=('ajustes',lambda s:s.str.contains('7').sum()),ultima_ge=('ultima_ge_primera','sum')))
print(o.ajustes.value_counts().head(12))
print(o[o.ira_identica==False].groupby('fy').apply(lambda x:pd.Series({'dif':len(x),'ratio_suma/max':(x.ira_sum.sum()/x.ira_max.sum())})))
# caso Chachagui 2016 sem 43
print(d[(d.fy==2016)&(d.cod_mun=='52240')&(d.semana==43)][['excel_row','fec_not','cod_sub','num_con','iracext_1','iracext_2','iracext_3','totcext_1','totcext_2','totcext_3','ajuste','fec_aju']])
# num_con de las filas: relacion con numero de filas por prestador-semana en años sin repeticion
print(d[d.fy==2022].groupby('key').num_con.agg(['min','max','count']).head(5))
print(d[d.fy==2022][['fec_not','num_con','ajuste','fec_aju']].head(5))
