import sys,json,csv,unicodedata
sys.path.insert(0,'.')
from xlsx_stream import *
B="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/"
f,tag=sys.argv[1],sys.argv[2]
def norm(s): return unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().strip().lower()
z,sh=sheets(B+f); sst=shared_strings(z)
name=[n for n in sh if (norm(n).startswith('nuevampal') or norm(n).startswith('pobmunicipal'))][0]
cm={}; ready=False
out=csv.writer(open(f'dane_{tag}.csv','w',newline='',encoding='utf-8'))
nrows=0; nar=0; areas=set(); years=set(); mp=set(); prev=None
def idx(s,a):
    for k in (f'{s}_{a}', f'{s} {a} anos', f'{s} {a} ano'):
        if k in cm: return cm[k]
for rn,r in rows(z,sh[name],sst):
    if not ready:
        if rn<=12 and any(norm(v)=='mpio' for v in r.values()):
            for i,v in r.items(): cm.setdefault(norm(v),i)
            prev=rn
            if tag=='a': ready=True
            continue
        if tag=='b' and prev is not None and rn==prev+1:
            for i,v in r.items(): cm[norm(v)]=i   # fila de nombres de campo (edades simples)
            ready=True
        if ready:
            json.dump({'sheet':name,'header_row':rn if tag=='a' else rn,'ncols':max(max(r),267),'keys':sorted(k for k in cm if any(c.isdigit() for c in k))[:6]},open(f'dcols_{tag}.json','w'))
            out.writerow(['excel_row','dp','mpio','municipio','anio','area']+[f'{s}_{a}' for s in ('hombres','mujeres','total') for a in range(5)]+['total_general','dp_name'])
        continue
    if not r: continue
    nrows+=1
    g=lambda k: r.get(cm.get(k))
    mpio=str(g('mpio')).strip().zfill(5)
    areas.add(g('area geografica')); years.add(g('ano')); mp.add(mpio)
    if mpio.startswith('52'):
        nar+=1
        row=[rn,g('dp'),mpio,g('dpmp'),g('ano'),g('area geografica')]
        for s in ('hombres','mujeres','total'):
            for a in range(5): row.append(r.get(idx(s,a)))
        row+= [r.get(cm.get('total')) if tag=='a' else r.get(7), g('dpnom')]
        out.writerow(row)
json.dump({'rows':nrows,'nar':nar,'areas':sorted(map(str,areas)),'years':sorted(map(str,years)),'n_mpio':len(mp)},open(f'dsum_{tag}.json','w'))
print('done',tag,nrows,nar)
