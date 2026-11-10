"""Extracción de población 0-4 años DANE por municipio-año de Nariño (solo lectura)."""
from __future__ import annotations
import csv, unicodedata
from pathlib import Path
from . import config as C
from .xlsx_stream import sheets, shared_strings, rows

DANE_BOOKS = {
    "a": ("DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx", "DANE_2005_2017"),
    "b": ("PPED-AreaSexoEdadMun-2018-2042_VP.xlsx", "DANE_2018_2042"),
}


def fold(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().strip().lower()


def extract(tag: str, out_dir: Path) -> dict:
    fname, libro = DANE_BOOKS[tag]
    z, sh = sheets(str(C.SOURCE_DIR / fname))
    sst = shared_strings(z)
    name = [n for n in sh if fold(n).startswith(("nuevampal", "pobmunicipal"))][0]
    cm = {}
    ready = False
    prev = None
    out_dir.mkdir(parents=True, exist_ok=True)
    fh = open(out_dir / f"dane_narino_{tag}.csv", "w", newline="", encoding="utf-8")
    w = csv.writer(fh)
    w.writerow(["excel_row", "dp", "mpio", "municipio", "anio", "area", "dane_libro", "hoja"] +
               [f"{s}_{a}" for s in ("hombres", "mujeres", "total") for a in range(5)])
    stats = dict(tag=tag, libro=libro, file=fname, sheet=name, rows=0, narino_rows=0)

    def idx(s, a):
        for k in (f"{s}_{a}", f"{s} {a} anos", f"{s} {a} ano"):
            if k in cm:
                return cm[k]
    for rn, r in rows(z, sh[name], sst):
        if not ready:
            if rn <= 12 and any(fold(v) == "mpio" for v in r.values()):
                for i, v in r.items():
                    cm.setdefault(fold(v), i)
                prev = rn
                if tag == "a":
                    ready = True
                continue
            if tag == "b" and prev is not None and rn == prev + 1:
                for i, v in r.items():
                    cm[fold(v)] = i          # fila de nombres de campo (edades simples)
                ready = True
            continue
        if not r:
            continue
        stats["rows"] += 1

        def g(k):
            return r.get(cm.get(k))
        mpio = str(g("mpio")).strip().zfill(5)
        if mpio.startswith("52"):
            stats["narino_rows"] += 1
            row = [rn, g("dp"), mpio, g("dpmp"), g("ano"), g("area geografica"), libro, name]
            for s in ("hombres", "mujeres", "total"):
                for a in range(5):
                    row.append(r.get(idx(s, a)))
            w.writerow(row)
    fh.close()
    return stats
