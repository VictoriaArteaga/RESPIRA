import sys,json
sys.path.insert(0,'.')
from xlsx_stream import *
B="C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA - copia/data/"
f,sheet,maxr=sys.argv[1],sys.argv[2],int(sys.argv[3])
z,sh=sheets(B+f); print(list(sh)); sst=shared_strings(z)
for rn,r in rows(z,sh[sheet],sst,max_rows=maxr):
    print(rn,[(i,v) for i,v in sorted(r.items())][:40])
