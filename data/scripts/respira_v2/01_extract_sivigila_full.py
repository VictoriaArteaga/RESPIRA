"""RESPIRA v2 / paso 1. Extrae de los libros SIVIGILA 995 (solo lectura) TODAS las columnas no personales
de las filas de Nariño (cod_mun 52xxx o departamento NARIÑO). Excluye contacto e identificación institucional.
Salida: data/respira_v2/interim/sivigila_full_{año}.csv (columnas propias de cada año)."""
import csv, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "data" / "scripts" / "pipeline"))
from respira_datasets import config as C
from respira_datasets.xlsx_stream import sheets, shared_strings, rows
from respira_datasets.sivigila import fold, clean_num_text

EXCLUDE = {"diligencia", "cargo", "telefono", "correo", "nit_upgd", "nom_upgd"}
OUT = ROOT / "data" / "respira_v2" / "interim"

def run(year):
    path = C.SOURCE_DIR / "SIVIGILA" / f"Datos_{year}_995.xlsx"
    z, sh = sheets(str(path)); sst = shared_strings(z)
    hdr = None; cmap = {}; keep = []
    n = kept = 0
    with open(OUT / f"sivigila_full_{year}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for rn, r in rows(z, sh[C.SIV_SHEET[year]], sst):
            if hdr is None:
                if rn <= 6 and any(fold(v) == "cod_eve" for v in r.values()):
                    hdr = rn
                    for i, v in r.items():
                        k = fold(v)
                        if k and k not in cmap: cmap[k] = i
                    keep = [k for k in cmap if k not in EXCLUDE]
                    w.writerow(["excel_row"] + keep)
                continue
            if not r: continue
            n += 1
            g = lambda k: r.get(cmap[k]) if k in cmap else None
            cm = clean_num_text(g("cod_mun")) or ""
            if cm: cm = cm.zfill(5)
            if not (cm.startswith("52") or fold(g("ndep_notif") or "") == "narino"): continue
            kept += 1
            w.writerow([rn] + [cm if k == "cod_mun" else ("" if g(k) is None else str(g(k)).strip()) for k in keep])
    return year, n, kept, len(keep)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time()
    with Pool(6) as p:
        for res in p.imap_unordered(run, sorted(C.YEARS, reverse=True)):
            print(res, flush=True)
    print("seg", round(time.time() - t))
