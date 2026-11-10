"""RESPIRA v2 / paso 6. dataset_climatico: variables IDEAM semanales por municipio (2012-2022) y evaluación de cobertura/calidad.
Reglas (sin imputación ni interpolación; ausencia = NA):
- Semana = calendario epidemiológico derivado (calendario_epidemiologico_2012_2022.csv).
- temp_min = mín de TSSM_MN_D; temp_max = máx de TSSM_MX_D; temp_media = media de TSSM_MEDIA_D; humedad = media de HR_CAL_MEDIA_D
  -> valor solo si >=6 de 7 días válidos.  precipitacion = suma de PTPM_CON_INTER -> solo si 7 de 7 días.
- Días fuera de rango físico se anulan (NA) y se cuentan. Estación con incoherencia térmica (mín<=media<=máx, tolerancia 0.5 C) en >2% de
  los días queda SERIE_NO_CONFIABLE para temperatura.
- Un municipio usa UNA estación por variable para todo el periodo: entre las estaciones que el catálogo IDEAM ubica en ese municipio,
  la de más semanas válidas (desempate: menor distancia a la cabecera). No se usan estaciones de otros municipios.
- 'apta' = cobertura >=80% de las 574 semanas y estación confiable. Unidades/etiquetas de precipitación y humedad NO confirmadas por IDEAM."""
from datetime import timedelta
from pathlib import Path
import sys
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2"
SRC = ROOT.parent / "RESPIRA - copia" / "data"
cal = pd.read_csv(OUT / "calendario_epidemiologico_2012_2022.csv", parse_dates=["semana_inicio", "semana_fin"])
geo = pd.read_csv(OUT / "dataset_geografico.csv", dtype={"codigo_divipola": str})
est = pd.read_csv(OUT / "estacion_municipio.csv", dtype={"codigo_divipola_catalogo": str})
est = est[est.codigo_divipola_catalogo.notna()]

days = []
for r in cal.itertuples():
    for k in range(7):
        days.append((r.semana_inicio + timedelta(days=k), r.anio, r.semana_epidemiologica))
daymap = pd.DataFrame(days, columns=["fecha", "anio", "semana_epidemiologica"]).set_index("fecha")
NWEEKS = len(cal)

VARS = {  # nombre: (prefijo archivo, carpeta, agregación, mín. días, rango físico)
    "temp_min": ("TSSM_MN_D", "TemperaturaNacionalDiaria", "min", 6, (-10, 45)),
    "temp_max": ("TSSM_MX_D", "TemperaturaNacionalDiaria", "max", 6, (-10, 50)),
    "temp_media": ("TSSM_MEDIA_D", "TemperaturaNacionalDiaria", "mean", 6, (-10, 45)),
    "humedad_relativa": ("HR_CAL_MEDIA_D", "MetereologiaNacionalDiaria", "mean", 6, (0, 100)),
    "precipitacion": ("PTPM_CON_INTER", "PrecipitacionNacionalDiaria", "sum", 7, (0, 1000)),
}


def read_daily(prefix, folder, code):
    p = SRC / folder / f"{prefix}@{code}.data"
    if not p.exists():
        return None
    d = pd.read_csv(p, sep="|", dtype=str)
    d["fecha"] = pd.to_datetime(d["Fecha"].str[:10], errors="coerce")
    d["v"] = pd.to_numeric(d["Valor"], errors="coerce")
    n_dup = int(d["fecha"].duplicated().sum())
    d = d.dropna(subset=["fecha"]).drop_duplicates("fecha").set_index("fecha")["v"]
    return d, n_dup


daily, info = {}, []
for r in est.itertuples():
    for var, (pre, folder, how, mind, rng) in VARS.items():
        res = read_daily(pre, folder, r.codigo_estacion)
        if res is None:
            continue
        s, n_dup = res
        w = s.loc[(s.index >= daymap.index.min()) & (s.index <= daymap.index.max())]
        fuera = int(((w < rng[0]) | (w > rng[1])).sum())
        s = s.where((s >= rng[0]) & (s <= rng[1]))
        daily[(r.codigo_estacion, var)] = s
        info.append(dict(codigo_estacion=r.codigo_estacion, variable=var, archivo=f"{pre}@{r.codigo_estacion}.data", fechas_duplicadas=n_dup,
                         dias_2012_2022_con_valor=int(w.notna().sum()), dias_fuera_de_rango=fuera,
                         minimo=float(np.nanmin(w)) if w.notna().any() else np.nan, maximo=float(np.nanmax(w)) if w.notna().any() else np.nan,
                         media=float(np.nanmean(w)) if w.notna().any() else np.nan))
info = pd.DataFrame(info)

# coherencia térmica por estación
inc = {}
for code in est.codigo_estacion:
    if all((code, v) in daily for v in ("temp_min", "temp_media", "temp_max")):
        t = pd.concat([daily[(code, "temp_min")], daily[(code, "temp_media")], daily[(code, "temp_max")]], axis=1, keys=["mn", "md", "mx"]).dropna()
        t = t[(t.index >= daymap.index.min()) & (t.index <= daymap.index.max())]
        bad = (t.mn > t.mx) | (t.md < t.mn - 0.5) | (t.md > t.mx + 0.5)
        inc[code] = (len(t), float(bad.mean()) if len(t) else np.nan, float((t.mn == t.mx).mean()) if len(t) else np.nan)


def weekly(s, how, mind):
    m = daymap.join(s.rename("v"))
    g = m.groupby(["anio", "semana_epidemiologica"])["v"]
    out = pd.DataFrame({"n_dias": g.count(), "valor": g.agg(how)})
    out.loc[out.n_dias < mind, "valor"] = np.nan
    return out


W, cov = {}, []
for (code, var), s in daily.items():
    pre, folder, how, mind, rng = VARS[var]
    w = weekly(s, how, mind)
    W[(code, var)] = w
    ok = w["valor"].notna()
    por_anio = ok.groupby(level=0).mean()
    n_inc, p_inc, p_mnmx = inc.get(code, (np.nan, np.nan, np.nan))
    no_conf = var.startswith("temp") and code in inc and (p_inc > 0.02 or p_mnmx > 0.5)
    cov.append(dict(codigo_estacion=code, variable=var, semanas_validas=int(ok.sum()), pct_semanas_validas=round(100 * ok.mean(), 1),
                    anios_con_ge80pct=int((por_anio >= 0.8).sum()), dias_con_incoherencia_termica_pct=None if np.isnan(p_inc) else round(100 * p_inc, 1),
                    pct_dias_min_igual_max=None if np.isnan(p_mnmx) else round(100 * p_mnmx, 1),
                    estado_calidad="SERIE_NO_CONFIABLE" if no_conf else "SIN_ALERTAS_AUTOMATICAS"))
cov = pd.DataFrame(cov).merge(info, on=["codigo_estacion", "variable"])
cov = cov.merge(est[["codigo_estacion", "nombre_estacion", "codigo_divipola_catalogo", "distancia_a_cabecera_km", "altitud_estacion_m", "estado_catalogo"]], on="codigo_estacion")
cov["etiqueta_confirmada_por_ideam"] = ~cov.variable.isin(["precipitacion", "humedad_relativa"])
cov.to_csv(OUT / "climatico_cobertura_estaciones.csv", index=False, encoding="utf-8-sig")

# selección de estación por municipio y variable
sel = []
for mun in geo.codigo_divipola:
    for var in VARS:
        c = cov[(cov.codigo_divipola_catalogo == mun) & (cov.variable == var)]
        if c.empty:
            sel.append(dict(codigo_divipola=mun, variable=var, codigo_estacion=None, motivo="SIN_ESTACION_CON_ARCHIVO_EN_EL_MUNICIPIO"))
            continue
        c = c.sort_values(["semanas_validas", "distancia_a_cabecera_km"], ascending=[False, True])
        ok = c[c.estado_calidad != "SERIE_NO_CONFIABLE"]
        if ok.empty:
            b = c.iloc[0]
            sel.append(dict(codigo_divipola=mun, variable=var, codigo_estacion=None, motivo="SERIE_NO_CONFIABLE:" + str(b.codigo_estacion)))
            continue
        b = ok.iloc[0]
        apta = b.pct_semanas_validas >= 80
        sel.append(dict(codigo_divipola=mun, variable=var, codigo_estacion=b.codigo_estacion, nombre_estacion=b.nombre_estacion,
                        distancia_a_cabecera_km=b.distancia_a_cabecera_km, altitud_estacion_m=b.altitud_estacion_m,
                        semanas_validas=b.semanas_validas, pct_semanas_validas=b.pct_semanas_validas,
                        apta=bool(apta), motivo="APTA" if apta else "COBERTURA_MENOR_80PCT"))
sel = pd.DataFrame(sel)
sel.to_csv(OUT / "climatico_estacion_por_municipio.csv", index=False, encoding="utf-8-sig")

grid = geo[["codigo_divipola", "municipio"]].assign(k=1).merge(cal[["anio", "semana_epidemiologica"]].assign(k=1), on="k").drop(columns="k")
ds = grid.copy()
for var in VARS:
    parts = []
    for r in sel[sel.variable == var].itertuples():
        if r.codigo_estacion is None or pd.isna(r.codigo_estacion):
            w = pd.DataFrame(index=pd.MultiIndex.from_frame(cal[["anio", "semana_epidemiologica"]]), columns=["valor", "n_dias"], dtype=float)
            w["estado"] = r.motivo.split(":")[0]
        else:
            w = W[(r.codigo_estacion, var)].copy()
            w["estado"] = np.where(w.valor.notna(), "OBSERVADO", np.where(w.n_dias == 0, "SIN_DATO", "COBERTURA_DIARIA_INSUFICIENTE"))
        w["codigo_divipola"] = r.codigo_divipola
        w["estacion"] = r.codigo_estacion
        parts.append(w.reset_index())
    t = pd.concat(parts).rename(columns={"valor": var, "n_dias": f"{var}_n_dias", "estado": f"{var}_estado", "estacion": f"{var}_estacion"})
    ds = ds.merge(t, on=["codigo_divipola", "anio", "semana_epidemiologica"], how="left")
ds["precipitacion_y_humedad_etiqueta_sin_confirmar"] = True
ds = ds.sort_values(["codigo_divipola", "anio", "semana_epidemiologica"])
ds.to_csv(OUT / "dataset_climatico.csv", index=False, encoding="utf-8-sig")

print("filas", len(ds))
for var in VARS:
    s = sel[sel.variable == var]
    print(f"{var:17s} municipios con estación utilizable: {s.codigo_estacion.notna().sum():2d}  aptos(>=80%): {int(s.apta.fillna(False).sum()):2d}  "
          f"semanas observadas: {int(ds[var].notna().sum())}")
print(cov[cov.variable == "humedad_relativa"][["codigo_estacion", "pct_semanas_validas", "dias_fuera_de_rango", "minimo", "maximo", "media"]].round(1).to_string(index=False))
print("no confiables:", cov[cov.estado_calidad == "SERIE_NO_CONFIABLE"][["codigo_estacion", "variable", "dias_con_incoherencia_termica_pct", "pct_dias_min_igual_max"]].values.tolist())
