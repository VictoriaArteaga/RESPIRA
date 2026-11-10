import sys, json, csv, collections, unicodedata
sys.path.insert(0,'.')
from xlsx_stream import *
D="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/SIVIGILA/"
SHEET={2012:'995 52',2013:'Hoja1',2014:'Hoja1',2015:'Hoja1',2016:'Hoja1',2017:'EVENTO 995',2018:'Hoja1',2019:'Final',2020:'995_2020_Depurada',2021:'ACUMULADO',2022:'995'}
y=int(sys.argv[1])
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().strip().lower()
    return s
z,sh=sheets(D+f"Datos_{y}_995.xlsx"); sst=shared_strings(z)
hdr=None; colmap={}
keep=['cod_eve','fec_not','semana','ano','cod_pre','cod_sub','cod_mun','num_con','iracext_1','iracext_2','iracext_3','tot_iraext','totcext_1','totcext_2','totcext_3','tot_exturg','ajuste','fec_aju','ndep_notif','nmun_notif','demanda']
out=open(f'nar_{y}.csv','w',newline='',encoding='utf-8')
w=csv.writer(out); w.writerow(['excel_row']+keep)
tot=0; by_sem=collections.Counter(); by_year=collections.Counter(); evt=collections.Counter(); muns=set(); nar=0; last=None; maxrow=0; firstdata=None
nar_ndep=collections.Counter(); ncols=0; blank=0
for rn,r in rows(z,sh[SHEET[y]],sst):
    maxrow=rn
    if hdr is None:
        if rn<=6 and any(norm(v)=='cod_eve' for v in r.values()):
            hdr=rn; ncols=max(r)
            for i,v in r.items(): colmap.setdefault(norm(v),i)
            json.dump({'header_row':rn,'cols':{norm(v):i for i,v in r.items()},'ncols':ncols},open(f'cols_{y}.json','w'))
        continue
    if not r: blank+=1; continue
    g=lambda k: r.get(colmap.get(k)) if colmap.get(k) else None
    tot+=1
    if firstdata is None: firstdata=rn
    sem=g('semana'); a=g('ano')
    by_sem[str(sem)]+=1; by_year[str(a)]+=1; evt[str(g('cod_eve'))]+=1
    cm=g('cod_mun'); cm=('' if cm is None else str(cm).strip()).replace('.0','').zfill(5)
    muns.add(cm); last=(rn,sem,a,cm)
    if cm.startswith('52'):
        nar+=1; nar_ndep[str(g('ndep_notif'))]+=1
        w.writerow([rn]+[ (cm if k=='cod_mun' else g(k)) for k in keep])
out.close()
json.dump({'year':y,'sheet':SHEET[y],'header_row':hdr,'ncols':ncols,'last_sheet_row_with_data':maxrow,'data_rows':tot,'blank_rows':blank,'nariño_rows':nar,'national_distinct_cod_mun':len(muns),
 'by_semana':dict(by_sem),'by_year_field':dict(by_year),'cod_eve':dict(evt),'ndep_notif_for_52':dict(nar_ndep),'last_data_row':last},open(f'sum_{y}.json','w'),ensure_ascii=True)
print('done',y,tot,nar)
