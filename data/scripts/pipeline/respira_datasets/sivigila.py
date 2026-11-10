"""Lectura/normalización de SIVIGILA 995 (solo lectura). Extrae únicamente campos NO personales."""
from __future__ import annotations
import csv, re, unicodedata
from pathlib import Path
from . import config as C
from .xlsx_stream import sheets, shared_strings, rows


def fold(s) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().strip().lower()


def clean_num_text(v):
    """Texto numérico normalizado; vacío -> None. Conserva 0 como '0'."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    if re.fullmatch(r"-?\d+\.0+", s):
        s = s.split(".")[0]
    return s


def extract_year(year: int, out_dir: Path) -> dict:
    """Recorre la hoja de detalle del libro del año y escribe sivigila_narino_{year}.csv (+ resumen)."""
    path = C.SOURCE_DIR / "SIVIGILA" / f"Datos_{year}_995.xlsx"
    sheet = C.SIV_SHEET[year]
    z, sh = sheets(str(path))
    sst = shared_strings(z)
    hdr = None
    colmap = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    outp = out_dir / f"sivigila_narino_{year}.csv"
    stats = dict(year=year, sheet=sheet, data_rows=0, non_995=0, kept=0, header_row=None, columns=[])
    with open(outp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["excel_row"] + C.SIV_KEEP)
        for rn, r in rows(z, sh[sheet], sst):
            if hdr is None:
                if rn <= 6 and any(fold(v) == "cod_eve" for v in r.values()):
                    hdr = rn
                    for i, v in r.items():
                        colmap.setdefault(fold(v), i)
                    stats["header_row"] = rn
                    stats["columns"] = sorted(colmap)
                continue
            if not r:
                continue
            stats["data_rows"] += 1

            def g(k):
                return r.get(colmap[k]) if k in colmap else None
            if str(g("cod_eve")).strip().replace(".0", "") != C.EVENT_CODE:
                stats["non_995"] += 1
            cm = clean_num_text(g("cod_mun")) or ""
            if cm:
                cm = cm.zfill(5)               # el libro 2012 guarda códigos sin cero inicial; vacío se conserva vacío
            nd = fold(g("ndep_notif") or "")
            if not (cm.startswith("52") or nd == "narino"):
                continue
            stats["kept"] += 1
            vals = []
            for k in C.SIV_KEEP:
                v = cm if k == "cod_mun" else g(k)
                vals.append("" if v is None else str(v).strip())
            w.writerow([rn] + vals)
    stats["file"] = path.name
    return stats
