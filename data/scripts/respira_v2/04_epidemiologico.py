"""RESPIRA v2 / paso 4. dataset_epidemiologico (malla completa municipio x año x semana, 2012-2022) y perfil de gravedad.
Reglas: ausencia de fila = NA (SIN_FILA), nunca 0; celda vacía en el numerador = NA (no 0); se conservan los dos
consolidados de reportes repetidos (suma y último reporte por UPGD/sede, orden por num_con); el principal es el último reporte
(supuesto: el reporte posterior corrige al anterior; pendiente de confirmar por INS) y se marca dónde difieren.
Grupo 0-4 = campos _1+_2+_3 (<1, 1, 2-4 años según estructura INS 2016)."""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2"
geo = pd.read_csv(OUT / "dataset_geografico.csv", dtype={"codigo_divipola": str})
cal = pd.read_csv(OUT / "calendario_epidemiologico_2012_2022.csv")
VALID = set(geo.codigo_divipola)

fr = []
for y in range(2012, 2023):
    d = pd.read_csv(OUT / "interim" / f"sivigila_full_{y}.csv", dtype=str)
    d["anio_libro"] = y
    fr.append(d)
a = pd.concat(fr, ignore_index=True)


def num(c):
    return pd.to_numeric(a[c], errors="coerce") if c in a else pd.Series(np.nan, index=a.index)


a["anio"] = num("ano")
a["semana_n"] = num("semana")
a["num_con_n"] = num("num_con")
a["pre"] = a["cod_pre"].fillna("").str.replace(r"\D", "", regex=True).str.lstrip("0")
a["sub"] = a["cod_sub"].fillna("").str.replace(r"\D", "", regex=True).str.lstrip("0")


def g3(p):
    x = pd.concat([num(f"{p}_{i}") for i in (1, 2, 3)], axis=1)
    return x.sum(axis=1, min_count=3)          # NA si falta cualquiera de los tres


a["ira"] = g3("iracext")
a["consultas"] = g3("totcext")
a["hosp_irag"] = g3("grupoh")
a["uci_irag"] = g3("irauci")
a["muertes_ira"] = g3("mteira")
a["territorio_incongruente"] = (~a["ndep_notif"].fillna("").str.upper().str.contains("NARI")) & a["cod_mun"].isin(VALID)

# filas no asignables: se guardan aparte, no se descartan en silencio
wk_max = cal.groupby("anio").semanas_en_anio.first().to_dict()
bad_mun = ~a["cod_mun"].isin(VALID)
bad_wk = (a["semana_n"].isna() | (a["semana_n"] < 1) | (a["semana_n"] > a["anio"].map(wk_max))
          | (a["anio"] != a["anio_libro"]))
mask = bad_mun | bad_wk
na = a.loc[mask, ["anio_libro", "excel_row", "cod_mun", "nmun_notif", "ndep_notif", "anio", "semana",
                  "iracext_1", "iracext_2", "iracext_3"]].copy()
na["motivo"] = np.where(bad_mun[mask], "COD_MUN_NO_ES_DE_NARINO", "SEMANA_O_ANIO_FUERA_DE_CALENDARIO")
na.to_csv(OUT / "sivigila_filas_no_asignables.csv", index=False, encoding="utf-8-sig")
a = a[~mask].copy()
a["semana_n"] = a["semana_n"].astype(int)
a["anio"] = a["anio"].astype(int)

K = ["cod_mun", "anio", "semana_n"]


def consolidar(df, var):
    """Por municipio-semana: suma, último reporte (por UPGD/sede, mayor num_con), nº de filas vacías y ambigüedad."""
    d = df[K + ["pre", "sub", "num_con_n", var]].copy()
    d["vacio"] = d[var].isna()
    s = d.groupby(K).agg(suma=(var, lambda x: x.sum(min_count=1)), n_vacias=("vacio", "sum"), n_filas=(var, "size"))
    gk = K + ["pre", "sub"]
    d["mx"] = d.groupby(gk)["num_con_n"].transform("max")
    tope = d[(d["num_con_n"] == d["mx"]) | d["mx"].isna()]
    g = tope.groupby(gk)[var]
    cnt = pd.DataFrame({"n_tope": g.size(), "dist": g.nunique(dropna=False)})
    cnt["ambiguo"] = (cnt["n_tope"] > 1) & (cnt["dist"] > 1)
    ult = g.agg(lambda x: x.iloc[0] if x.nunique(dropna=False) == 1 else np.nan)
    gl = pd.concat([ult.rename("v"), cnt["ambiguo"]], axis=1).reset_index()
    out = gl.groupby(K).agg(ultimo=("v", lambda x: x.sum(min_count=1)), n_grupos=("v", "size"), n_amb=("ambiguo", "sum"))
    r = s.join(out)
    r.loc[r["n_amb"] > 0, "ultimo"] = np.nan
    return r


R = {v: consolidar(a, v) for v in ("ira", "consultas", "hosp_irag", "uci_irag", "muertes_ira")}
base = R["ira"].rename(columns={"suma": "ira_0_4_suma", "ultimo": "ira_0_4_ultimo_reporte", "n_filas": "n_filas_reportadas",
                                "n_vacias": "n_filas_con_vacio_ira", "n_grupos": "n_grupos_upgd_sede",
                                "n_amb": "n_grupos_orden_no_determinable"})
base["consultas_0_4_totales_ultimo_reporte"] = R["consultas"]["ultimo"]
base["consultas_0_4_totales_suma"] = R["consultas"]["suma"]
inc = a.groupby(K)["territorio_incongruente"].sum().rename("n_filas_territorio_incongruente")
base = base.join(inc).reset_index().rename(columns={"cod_mun": "codigo_divipola", "semana_n": "semana_epidemiologica"})

grid = (geo[["codigo_divipola", "municipio"]].assign(k=1)
        .merge(cal[["anio", "semana_epidemiologica", "semana_inicio", "semana_fin", "estado_calendario"]].assign(k=1), on="k")
        .drop(columns="k"))
ds = grid.merge(base, on=["codigo_divipola", "anio", "semana_epidemiologica"], how="left")
ds["n_filas_reportadas"] = ds["n_filas_reportadas"].fillna(0).astype(int)
ds["tiene_reportes_repetidos"] = ds["n_filas_reportadas"] > ds["n_grupos_upgd_sede"].fillna(0)
ds["suma_difiere_de_ultimo"] = ds["tiene_reportes_repetidos"] & (ds["ira_0_4_suma"] != ds["ira_0_4_ultimo_reporte"])
ds["ira_0_4"] = ds["ira_0_4_ultimo_reporte"]            # variable principal (ver docstring)
ds["estado_dato_ira"] = np.select(
    [ds.n_filas_reportadas == 0, ds.ira_0_4.isna() & (ds.n_grupos_orden_no_determinable > 0), ds.ira_0_4.isna()],
    ["SIN_FILA", "ULTIMO_REPORTE_NO_DETERMINABLE", "VACIO_EN_FUENTE"], "OBSERVADO")
ds["proporcion_ira_sobre_consultas"] = np.where(ds.consultas_0_4_totales_ultimo_reporte > 0,
                                                ds.ira_0_4 / ds.consultas_0_4_totales_ultimo_reporte, np.nan)
ds["regimen"] = np.select([ds.anio <= 2019, ds.anio <= 2021], ["PRE_PANDEMIA", "PANDEMIA"], "POST_PANDEMIA")
cols = ["codigo_divipola", "municipio", "anio", "semana_epidemiologica", "semana_inicio", "semana_fin", "estado_calendario",
        "regimen", "ira_0_4", "estado_dato_ira", "ira_0_4_suma", "ira_0_4_ultimo_reporte", "tiene_reportes_repetidos",
        "suma_difiere_de_ultimo", "n_filas_reportadas", "n_grupos_upgd_sede", "n_grupos_orden_no_determinable",
        "n_filas_con_vacio_ira", "consultas_0_4_totales_ultimo_reporte", "consultas_0_4_totales_suma",
        "proporcion_ira_sobre_consultas", "n_filas_territorio_incongruente"]
ds = ds[cols].sort_values(["codigo_divipola", "anio", "semana_epidemiologica"])
ds.to_csv(OUT / "dataset_epidemiologico.csv", index=False, encoding="utf-8-sig")

# gravedad experimental (no entra al entrenamiento sin decisión)
gr = grid[["codigo_divipola", "municipio", "anio", "semana_epidemiologica"]].copy()
for v, nm in (("hosp_irag", "hosp_irag_0_4"), ("uci_irag", "uci_irag_0_4"), ("muertes_ira", "muertes_ira_0_4")):
    t = (R[v][["ultimo"]].rename(columns={"ultimo": nm}).reset_index()
         .rename(columns={"cod_mun": "codigo_divipola", "semana_n": "semana_epidemiologica"}))
    gr = gr.merge(t, on=["codigo_divipola", "anio", "semana_epidemiologica"], how="left")
gr = gr.merge(ds[["codigo_divipola", "anio", "semana_epidemiologica", "estado_dato_ira"]],
              on=["codigo_divipola", "anio", "semana_epidemiologica"])
gr.to_csv(OUT / "dataset_gravedad_experimental.csv", index=False, encoding="utf-8-sig")

p = []
for v in ("hosp_irag_0_4", "uci_irag_0_4", "muertes_ira_0_4"):
    obs = gr[gr[v].notna()]
    por_mun = obs.groupby("codigo_divipola")[v].sum()
    top2 = por_mun.sort_values(ascending=False).head(2).sum() / max(por_mun.sum(), 1)
    sem_mun = obs.groupby("codigo_divipola")[v].apply(lambda x: (x > 0).mean())
    p.append(dict(variable=v, municipio_semanas_observadas=len(obs), prop_obs_mayor_0=round((obs[v] > 0).mean(), 4),
                  total_2012_2022=int(obs[v].sum()), municipios_con_algun_valor=int((por_mun > 0).sum()),
                  concentracion_top2_municipios=round(top2, 3),
                  municipios_con_prop_semanas_mayor0_ge10pct=int((sem_mun >= 0.10).sum()),
                  maximo_en_una_semana_municipio=int(obs[v].max())))
prof = pd.DataFrame(p)
prof.to_csv(OUT / "perfil_variables_gravedad.csv", index=False, encoding="utf-8-sig")
print(prof.T.to_string())
print("malla", len(ds), ds.estado_dato_ira.value_counts().to_dict())
print("no asignables:", len(na), na.motivo.value_counts().to_dict())
print("suma!=ultimo en", int(ds.suma_difiere_de_ultimo.sum()), "mun-semanas; con repetidos", int(ds.tiene_reportes_repetidos.sum()))
print(ds.groupby("anio").ira_0_4.sum().astype(int).to_dict())
