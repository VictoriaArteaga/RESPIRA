import sys,unicodedata
sys.path.insert(0,'.')
from xlsx_stream import *
B="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/"
z,sh=sheets(B+"PPED-AreaSexoEdadMun-2018-2042_VP.xlsx"); sst=shared_strings(z)
name=list(sh)[2]
for rn,r in rows(z,sh[name],sst,max_rows=11):
    items=sorted(r.items())
    print(rn,len(items),[(i,v) for i,v in items if i<=14 or 100<i<=104 or i>=205])
