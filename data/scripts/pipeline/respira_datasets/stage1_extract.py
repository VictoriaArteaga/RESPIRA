"""Etapa 1: lectura de fuentes (SIVIGILA y DANE) -> intermedios en data/interim/. Paralelo, solo lectura."""
from __future__ import annotations
import json, time
from multiprocessing import Pool
from . import config as C, sivigila, dane


def _siv(y):
    return ("siv", y, sivigila.extract_year(y, C.INTERIM_DIR))


def _dane(t):
    return ("dane", t, dane.extract(t, C.INTERIM_DIR))


def run():
    t0 = time.time()
    C.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    with Pool(6) as p:
        res = [p.apply_async(_dane, (t,)) for t in ("b", "a")] + [p.apply_async(_siv, (y,)) for y in sorted(C.YEARS, reverse=True)]
        out = [r.get() for r in res]
    summ = {f"{k}_{i}": s for k, i, s in out}
    (C.INTERIM_DIR / "stage1_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, s in summ.items():
        print(k, {a: b for a, b in s.items() if a != "columns"})
    print("segundos", round(time.time() - t0))


if __name__ == "__main__":
    run()
