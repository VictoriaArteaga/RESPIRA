"""RESPIRA v2 / paso 9. Extensión 2023-2025 con LO QUE ES PÚBLICO (sin tocar los archivos 2012-2022 existentes).
Genera archivos nuevos:
  calendario_epidemiologico_2012_2025.csv   (regla SE1 contiene 4-ene; anclas INS 2024-2025 verificadas)
  dataset_poblacional_2012_2025.csv         (DANE, misma serie 2018-2042)
  climatico_publico_empalme_2022.csv        (comparación público vs. serie histórica en 2022)
  dataset_climatico_publico_2023_2025.csv   (clima semanal por municipio, IDEAM datos.gov.co, estaciones automáticas)
  dataset_contexto_2023_2025.csv            (malla municipio-semana 2023-2025: calendario + población + clima; IRA NO DISPONIBLE)
  extension_2023_2025_manifest.json
El evento 995 de SIVIGILA de 2023-2025 NO es público: la columna de IRA queda vacía y esas filas no sirven para entrenar."""
import json
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2"
PUB = OUT / "fuentes_oficiales"
YEARS_NEW = (2023, 2024, 2025)
INS_ANCLAS = {(2024, 15): ("2024-04-07", "2024-04-13"), (2025, 1): ("2024-12-29", "2025-01-04"),
              (2025, 6): ("2025-02-02", "2025-02-08"), (2025, 48): ("2025-11-23", "2025-11-29")}


def start_se1(y):
    j4 = date(y, 1, 4)
    return j4 - timedelta(days=(j4.weekday() + 1) % 7)


# ------------------------------------------------------------------ calendario 2012-2025
old = pd.read_csv(OUT / "calendario_epidemiologico_2012_2022.csv", parse_dates=["semana_inicio", "semana_fin"])
rows = []
for y in YEARS_NEW:
    n = (start_se1(y + 1) - start_se1(y)).days // 7
    for w in range(1, n + 1):
        ini = start_se1(y) + timedelta(days=7 * (w - 1))
        rows.append((y, w, pd.Timestamp(ini), pd.Timestamp(ini + timedelta(days=6)), n))
new = pd.DataFrame(rows, columns=["anio", "semana_epidemiologica", "semana_inicio", "semana_fin", "semanas_en_anio"])
for (y, w), (a, b) in INS_ANCLAS.items():
    r = new[(new.anio == y) & (new.semana_epidemiologica == w)].iloc[0]
    assert (str(r.semana_inicio.date()), str(r.semana_fin.date())) == (a, b), (y, w)   # la regla reproduce las fechas citadas por el INS
new["estado_calendario"] = new.anio.map({2023: "DERIVADO_SIN_ANCLA_OFICIAL_REQUIERE_CONFIRMACION_INS",
                                         2024: "DERIVADO_CON_ANCLA_BOLETIN_INS_SE15", 2025: "DERIVADO_CON_ANCLAS_BOLETIN_INS_SE1_SE6_SE48"})
new["fuente"] = "Regla SE1 contiene 4-ene (MMWR/INS); anclas: " + new.anio.map({2023: "ninguna", 2024: "SE15", 2025: "SE1, SE6, SE48"})
cal = pd.concat([old, new], ignore_index=True)
cal.to_csv(OUT / "calendario_epidemiologico_2012_2025.csv", index=False, encoding="utf-8-sig")
cal_new = cal[cal.anio.isin(YEARS_NEW)].reset_index(drop=True)

geo = pd.read_csv(OUT / "dataset_geografico.csv", dtype={"codigo_divipola": str})

# ------------------------------------------------------------------ población 2012-2025
fr = [pd.read_csv(ROOT / "data" / "interim" / f"dane_narino_{t}.csv", dtype=str) for t in "ab"]
d = pd.concat(fr, ignore_index=True)
d = d[d["area"] == "Total"].copy()
for c in [c for c in d.columns if c.startswith("total_")]:
    d[c] = pd.to_numeric(d[c])
d["anio"] = d["anio"].astype(int)
d = d[(d.anio >= 2012) & (d.anio <= 2025)]
pop = pd.DataFrame({"codigo_divipola": d["mpio"], "anio": d["anio"], "serie_dane": d["dane_libro"]})
for i in range(5):
    pop[f"poblacion_{i}_anios"] = d[f"total_{i}"].values
pop["poblacion_0_4"] = pop[[f"poblacion_{i}_anios" for i in range(5)]].sum(axis=1)
pop = pop.merge(geo[["codigo_divipola", "municipio"]], on="codigo_divipola").sort_values(["codigo_divipola", "anio"])
pop["variacion_interanual_pct"] = pop.groupby("codigo_divipola")["poblacion_0_4"].pct_change().mul(100).round(2)
pop["cambio_de_serie"] = pop["anio"].eq(2018)
assert len(pop) == 64 * 14 and not pop.duplicated(["codigo_divipola", "anio"]).any()
pop.to_csv(OUT / "dataset_poblacional_2012_2025.csv", index=False, encoding="utf-8-sig")

# ------------------------------------------------------------------ clima público
def nz(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^A-Z ]", "", s).strip()


MANUAL = {"TUMACO": "52835", "SAN ANDRES DE TUMACO": "52835", "EL TABLON": "52258", "EL TABLON DE GOMEZ": "52258", "SANTA CRUZ": "52699", "SANTACRUZ": "52699"}
name2code = {nz(r.municipio): r.codigo_divipola for r in geo.itertuples()}
VARS = {"temp_min": ("temperatura", "vmin", "min", 6, (-10, 45)), "temp_max": ("temperatura", "vmax", "max", 6, (-10, 50)),
        "temp_media": ("temperatura", "vmed", "mean", 6, (-10, 45)), "humedad_relativa": ("humedad", "vmed", "mean", 6, (0, 100)),
        "precipitacion": ("precipitacion", "vsuma", "sum", 7, (0, 1000))}
days = pd.DataFrame([(r.semana_inicio + timedelta(days=k), r.anio, r.semana_epidemiologica) for r in cal[cal.anio >= 2022].itertuples() for k in range(7)],
                    columns=["fecha", "anio", "semana_epidemiologica"]).set_index("fecha")

hist_sel = pd.read_csv(OUT / "climatico_estacion_por_municipio.csv", dtype={"codigo_divipola": str})
hist_sel = hist_sel[hist_sel.codigo_estacion.notna()].copy()
hist_sel["est"] = hist_sel.codigo_estacion.astype(float).astype(int)
hist_clim = pd.read_csv(OUT / "dataset_climatico.csv", dtype={"codigo_divipola": str})

series, meta = {}, []
for var, (fname, col, how, mind, rng) in VARS.items():
    f = pd.read_csv(PUB / f"ideam_publico_diario_{fname}.csv", dtype={"codigoestacion": str, "codigosensor": str})
    f["est"] = f.codigoestacion.astype(int)
    f["fecha"] = pd.to_datetime(f["dia"].str[:10])
    f["typical"] = f.groupby(["est", "codigosensor"])["n"].transform("median")
    f["dia_valido"] = f["n"] >= 0.8 * f["typical"]                       # día con ≥80% de las lecturas habituales de esa estación-sensor
    f.loc[(f[col] < rng[0]) | (f[col] > rng[1]), "dia_valido"] = False
    f["val"] = f[col].where(f["dia_valido"])
    best_sensor = f.groupby(["est", "codigosensor"])["dia_valido"].sum().reset_index().sort_values("dia_valido", ascending=False).drop_duplicates("est")
    f = f.merge(best_sensor[["est", "codigosensor"]], on=["est", "codigosensor"])
    f["cod_mun"] = f["municipio"].map(lambda m: MANUAL.get(nz(m)) or name2code.get(nz(m)))
    for est, g in f.groupby("est"):
        s = g.drop_duplicates("fecha").set_index("fecha")["val"]
        m = days.join(s.rename("v"))
        grp = m.groupby(["anio", "semana_epidemiologica"])["v"]
        w = pd.DataFrame({"n_dias": grp.count(), "valor": grp.agg(how)})
        w.loc[w.n_dias < mind, "valor"] = np.nan
        series[(est, var)] = w
        meta.append(dict(est=est, variable=var, nombre=g["nombreestacion"].iloc[0], municipio_portal=g["municipio"].iloc[0],
                         codigo_divipola=g["cod_mun"].iloc[0], sensor=g["codigosensor"].iloc[0], unidad=g["unidadmedida"].iloc[0],
                         semanas_validas_2023_2025=int(w.loc[w.index.get_level_values(0).isin(YEARS_NEW), "valor"].notna().sum())))
meta = pd.DataFrame(meta)
sin_mapa = meta[meta.codigo_divipola.isna()][["est", "municipio_portal"]].drop_duplicates()
print("estaciones sin DIVIPOLA por nombre:", sin_mapa.values.tolist())

# empalme 2022: estaciones históricas presentes en el portal
emp = []
for r in hist_sel.itertuples():
    key = (r.est, r.variable)
    if key not in series:
        continue
    pub = series[key]
    pub22 = pub.loc[2022]["valor"].rename("pub")
    h = hist_clim[(hist_clim.codigo_divipola == r.codigo_divipola) & (hist_clim.anio == 2022)].set_index("semana_epidemiologica")[r.variable].rename("serie_hist")
    j = pd.concat([pub22, h], axis=1).dropna()
    if len(j) >= 5:
        emp.append(dict(codigo_estacion=r.est, variable=r.variable, codigo_divipola=r.codigo_divipola, semanas_comparables_2022=len(j),
                        diferencia_media_pub_menos_hist=round(float((j.pub - j.serie_hist).mean()), 3), mae=round(float((j.pub - j.serie_hist).abs().mean()), 3),
                        correlacion=round(float(j.pub.corr(j.serie_hist)), 3), media_hist=round(float(j.serie_hist.mean()), 2)))
emp = pd.DataFrame(emp).drop_duplicates(["codigo_estacion", "variable"])
emp.to_csv(OUT / "climatico_publico_empalme_2022.csv", index=False, encoding="utf-8-sig")

# selección por municipio y variable (preferir la estación histórica de RESPIRA; si no está, la de más semanas válidas)
grid = geo[["codigo_divipola", "municipio"]].assign(k=1).merge(cal_new[["anio", "semana_epidemiologica"]].assign(k=1), on="k").drop(columns="k")
out = grid.copy()
resumen = {}
for var in VARS:
    parts, usados = [], []
    for mun in geo.codigo_divipola:
        cand = meta[(meta.variable == var) & (meta.codigo_divipola == mun)]
        hist = set(hist_sel[(hist_sel.codigo_divipola == mun) & (hist_sel.variable == var)].est)
        if cand.empty:
            continue
        cand = cand.assign(historica=cand.est.isin(hist)).sort_values(["historica", "semanas_validas_2023_2025"], ascending=False)
        c = cand.iloc[0]
        w = series[(c.est, var)].loc[list(YEARS_NEW)].reset_index()
        w["codigo_divipola"] = mun
        w[f"{var}_estacion"] = c.est
        w[f"{var}_estacion_historica_respira"] = bool(c.historica)
        parts.append(w.rename(columns={"valor": var, "n_dias": f"{var}_n_dias"}))
        usados.append((mun, int(c.est), bool(c.historica), int(c.semanas_validas_2023_2025)))
    t = pd.concat(parts)
    out = out.merge(t, on=["codigo_divipola", "anio", "semana_epidemiologica"], how="left")
    resumen[var] = {"municipios_con_estacion_publica": len(usados), "de_ellos_con_estacion_historica_de_respira": sum(u[2] for u in usados),
                    "municipios_con_>=50%_semanas_validas_2023_2025": sum(u[3] >= 0.5 * len(cal_new) for u in usados),
                    "semanas_validas_total": int(out[var].notna().sum())}
out["etiqueta_precipitacion_humedad"] = "unidad confirmada por el portal (mm, %); método automático horario/10 min, distinto de la serie convencional diaria histórica"
out = out.sort_values(["codigo_divipola", "anio", "semana_epidemiologica"])
out.to_csv(OUT / "dataset_climatico_publico_2023_2025.csv", index=False, encoding="utf-8-sig")

# ------------------------------------------------------------------ contexto 2023-2025
ctx = cal_new[["anio", "semana_epidemiologica", "semana_inicio", "semana_fin", "estado_calendario"]].merge(geo[["codigo_divipola", "municipio"]], how="cross")
ctx = ctx.merge(pop[["codigo_divipola", "anio", "poblacion_0_4", "serie_dane"]], on=["codigo_divipola", "anio"], how="left")
ctx = ctx.merge(out.drop(columns=["municipio"]), on=["codigo_divipola", "anio", "semana_epidemiologica"], how="left")
ctx["ira_0_4"] = np.nan
ctx["estado_dato_ira"] = "NO_DISPONIBLE_PUBLICAMENTE (evento 995 2023-2025 requiere solicitud al INS)"
ctx["usable_para_entrenar"] = False
ctx = ctx.sort_values(["codigo_divipola", "anio", "semana_epidemiologica"])
ctx.to_csv(OUT / "dataset_contexto_2023_2025.csv", index=False, encoding="utf-8-sig")

manifest = {"generado_utc": pd.Timestamp.now("UTC").isoformat(timespec="seconds"),
            "alcance": "extensión 2023-2025 solo con fuentes públicas; IRA (SIVIGILA 995) no disponible públicamente",
            "calendario": {"anclas_ins_verificadas": [f"SE{w} {y}: {a} a {b}" for (y, w), (a, b) in INS_ANCLAS.items()],
                           "semanas": {int(y): int(n) for y, n in cal_new.groupby("anio").size().items()}},
            "poblacion": {"anios": "2012-2025", "total_0_4_nariño": {int(a): int(b) for a, b in pop[pop.anio >= 2022].groupby("anio").poblacion_0_4.sum().items()}},
            "clima_publico": resumen, "empalme_2022": emp.to_dict("records"),
            "filas_contexto": int(len(ctx)), "ira_disponible_2023_2025": False}
(OUT / "extension_2023_2025_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps(resumen, ensure_ascii=False, indent=1))
print(emp.to_string(index=False))
print("contexto filas", len(ctx), "semanas", cal_new.groupby("anio").size().to_dict())
