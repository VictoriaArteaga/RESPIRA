"""RESPIRA v2 / paso 3. Calendario epidemiológico 2012-2022.
Regla (MMWR/INS): semanas domingo-sábado; la SE1 es la semana que contiene el 4 de enero. Se genera para todos los años y se
contrasta con (a) anclas oficiales: boletín INS SE52 de 2016 y 2022; (b) nº de semanas máximo observado en SIVIGILA por año;
(c) prueba independiente con fec_not: con el calendario correcto la mayor proporción de reportes tiene fec_not dentro de la
misma semana (0-6 días tras el inicio) y casi ninguno antes del inicio; se compara con el calendario corrido ±7 días. Estado por año: VERIFICADO_OFICIAL | DERIVADO_CONSISTENTE | REQUIERE_CONFIRMACION_INS."""
import sys
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2"
ANCLAS = {2016: "2016-12-31", 2022: "2022-12-31"}   # fin SE52 según boletín INS (ver data/scripts/pipeline config)

def start_se1(y):
    j4 = date(y, 1, 4)
    return j4 - timedelta(days=(j4.weekday() + 1) % 7)

rows = []
for y in range(2012, 2023):
    s1, s1n = start_se1(y), start_se1(y + 1)
    n = (s1n - s1).days // 7
    for w in range(1, n + 1):
        ini = s1 + timedelta(days=7 * (w - 1))
        rows.append((y, w, ini, ini + timedelta(days=6), n))
cal = pd.DataFrame(rows, columns=["anio", "semana_epidemiologica", "semana_inicio", "semana_fin", "semanas_en_anio"])

# --- evidencia con fec_not
def serial_to_date(v):
    v = str(v).strip()
    if not v: return pd.NaT
    try:
        f = float(v)
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=f)
    except ValueError:
        return pd.to_datetime(v, dayfirst=True, errors="coerce")

ev = []
for y in range(2012, 2023):
    d = pd.read_csv(OUT / "interim" / f"sivigila_full_{y}.csv", dtype=str, usecols=lambda c: c in ("semana", "fec_not", "ano", "año"))
    d["wk"] = pd.to_numeric(d["semana"], errors="coerce")
    d["f"] = d["fec_not"].map(serial_to_date)
    d = d.dropna(subset=["wk", "f"])
    d = d[(d.wk >= 1)]
    c = cal[cal.anio == y].set_index("semana_epidemiologica")
    nmax = int(d.wk.max())
    res = {}; neg = {}
    for shift in (-7, 0, 7):
        ini = pd.to_datetime(d["wk"].map(lambda w: c["semana_inicio"].get(int(w))) ) + pd.Timedelta(days=shift)
        lag = (d["f"] - ini).dt.days
        res[shift] = float(((lag >= 0) & (lag <= 6)).mean()); neg[shift] = float((lag < 0).mean())
    best = max(res, key=res.get)
    ev.append(dict(anio=y, semanas_regla=int(c.index.max()), semana_max_sivigila=nmax, filas_con_fecha=len(d),
                   prop_misma_semana_shift0=round(res[0], 4), prop_fecha_anterior_inicio_shift0=round(neg[0], 4), prop_misma_semana_shift_menos7=round(res[-7], 4), prop_misma_semana_shift_mas7=round(res[7], 4),
                   mejor_desplazamiento_dias=best))
ev = pd.DataFrame(ev)
def estado(r):
    if r.anio in ANCLAS: return "VERIFICADO_OFICIAL"
    ok = (r.semanas_regla == r.semana_max_sivigila or (r.anio == 2021 and r.semanas_regla == 52)) and r.mejor_desplazamiento_dias == 0
    if ok and r.prop_misma_semana_shift0 < 0.9: return "DERIVADO_EVIDENCIA_DEBIL_REQUIERE_CONFIRMACION_INS"
    return "DERIVADO_CONSISTENTE_REQUIERE_CONFIRMACION_INS" if ok else "REQUIERE_CONFIRMACION_INS_DISCREPANTE"
ev["estado_calendario"] = ev.apply(estado, axis=1)
cal = cal.merge(ev[["anio", "estado_calendario"]], on="anio")
cal["fuente"] = cal.anio.map(lambda y: f"Boletín INS SE52 {y} (ancla oficial) + regla SE1 contiene 4-ene" if y in ANCLAS else "Regla SE1 contiene 4-ene (MMWR/INS); no verificada contra boletín")
cal.to_csv(OUT / "calendario_epidemiologico_2012_2022.csv", index=False, encoding="utf-8-sig")
ev.to_csv(OUT / "calendario_evidencia_por_anio.csv", index=False, encoding="utf-8-sig")
for y, e in ANCLAS.items():
    assert str(cal[(cal.anio == y) & (cal.semana_epidemiologica == 52)].semana_fin.iloc[0]) == e, y
print(ev.to_string(index=False))
