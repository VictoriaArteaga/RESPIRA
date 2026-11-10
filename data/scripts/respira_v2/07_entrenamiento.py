"""RESPIRA v2 / paso 7. dataset_entrenamiento: una sola tabla municipio x año x semana con dos objetivos (t+2 y t+3).
Integra epidemiología, población, clima (solo estaciones/variables APTAS) y características temporales.
Sin imputación: los rezagos y objetivos son NA si la semana de origen no tiene dato. Los rezagos usan solo semanas pasadas."""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2"
epi = pd.read_csv(OUT / "dataset_epidemiologico.csv", dtype={"codigo_divipola": str}, parse_dates=["semana_inicio", "semana_fin"])
pob = pd.read_csv(OUT / "dataset_poblacional.csv", dtype={"codigo_divipola": str})
clim = pd.read_csv(OUT / "dataset_climatico.csv", dtype={"codigo_divipola": str})
sel = pd.read_csv(OUT / "climatico_estacion_por_municipio.csv", dtype={"codigo_divipola": str})
cal = pd.read_csv(OUT / "calendario_epidemiologico_2012_2022.csv")

CL = ["temp_min", "temp_max", "temp_media", "humedad_relativa", "precipitacion"]
k = ["codigo_divipola", "anio", "semana_epidemiologica"]
d = epi.merge(pob[["codigo_divipola", "anio", "poblacion_0_4", "serie_dane", "cambio_de_serie"]], on=["codigo_divipola", "anio"], how="left")
d = d.merge(clim[k + CL + [f"{v}_n_dias" for v in CL]], on=k, how="left")
for v in CL:   # solo variables aptas (>=80% de semanas, estación confiable)
    aptos = set(sel[(sel.variable == v) & (sel.apta == True)].codigo_divipola)
    d.loc[~d.codigo_divipola.isin(aptos), [v, f"{v}_n_dias"]] = np.nan
d = d.drop(columns=[f"{v}_n_dias" for v in CL if v not in ()])
d = d.sort_values(k).reset_index(drop=True)
d["indice_semana"] = d.groupby("codigo_divipola").cumcount()
g = d.groupby("codigo_divipola", sort=False)

# --- características epidemiológicas (solo pasado)
d["tasa_ira_notificada_x1000_menores5"] = d["ira_0_4"] / d["poblacion_0_4"] * 1000
for L in (1, 2, 3, 4):
    d[f"ira_lag{L}"] = g["ira_0_4"].shift(L)
d["ira_media_4s"] = g["ira_0_4"].transform(lambda x: x.rolling(4, min_periods=3).mean())
d["ira_media_8s"] = g["ira_0_4"].transform(lambda x: x.rolling(8, min_periods=6).mean())
d["ira_cambio_vs_lag1"] = d["ira_0_4"] - d["ira_lag1"]
d["ira_52s_atras"] = g["ira_0_4"].shift(52)      # en años de 53 semanas queda desfasada ~1 semana
d["proporcion_ira_lag1"] = g["proporcion_ira_sobre_consultas"].shift(1)
# --- clima: valor actual, rezagos 1-2 y media de 4 semanas (con min. 3 observadas)
for v in CL:
    gv = d.groupby("codigo_divipola", sort=False)[v]
    d[f"{v}_lag1"] = gv.shift(1)
    d[f"{v}_lag2"] = gv.shift(2)
    d[f"{v}_media_4s"] = gv.transform(lambda x: x.rolling(4, min_periods=3).mean())
# --- calendario
n = d["anio"].map(cal.groupby("anio").semanas_en_anio.first())
d["semana_sin"] = np.sin(2 * np.pi * d["semana_epidemiologica"] / n)
d["semana_cos"] = np.cos(2 * np.pi * d["semana_epidemiologica"] / n)
d["mes_aprox"] = (d["semana_inicio"] + pd.Timedelta(days=3)).dt.month
# --- objetivos (conteo notificado en t+2 y t+3; NA si esa semana no tiene dato)
g = d.groupby("codigo_divipola", sort=False)
d["objetivo_ira_t_mas_2"] = g["ira_0_4"].shift(-2)
d["objetivo_ira_t_mas_3"] = g["ira_0_4"].shift(-3)
d["objetivo_tasa_x1000_t_mas_2"] = g["tasa_ira_notificada_x1000_menores5"].shift(-2)
d["objetivo_tasa_x1000_t_mas_3"] = g["tasa_ira_notificada_x1000_menores5"].shift(-3)
d["semana_objetivo_t_mas_2"] = g["semana_fin"].shift(-2)
d["semana_objetivo_t_mas_3"] = g["semana_fin"].shift(-3)

# --- elegibilidad y partición sugerida
feat = ["ira_0_4", "ira_lag1", "ira_lag2", "ira_lag3", "ira_lag4"]
d["fila_completa_h2"] = d[feat + ["objetivo_ira_t_mas_2"]].notna().all(axis=1) & d["poblacion_0_4"].notna()
d["fila_completa_h3"] = d[feat + ["objetivo_ira_t_mas_3"]].notna().all(axis=1) & d["poblacion_0_4"].notna()
d["tiene_temperatura_t"] = d[["temp_min", "temp_max", "temp_media"]].notna().all(axis=1)
d["tiene_humedad_t"] = d["humedad_relativa"].notna()
d["tiene_precipitacion_t"] = d["precipitacion"].notna()
d["variables_clima_disponibles_t"] = d[CL].notna().sum(axis=1)
med = d[d.anio <= 2019].groupby("codigo_divipola")["ira_0_4"].median()
d["mediana_ira_semanal_2012_2019_municipio"] = d["codigo_divipola"].map(med)
d["municipio_volumen_ge10"] = d["mediana_ira_semanal_2012_2019_municipio"] >= 10
d["calendario_verificado_oficial"] = d["estado_calendario"].eq("VERIFICADO_OFICIAL")
d["split_sugerido"] = np.select([d.anio <= 2018, d.anio == 2019, d.anio <= 2021], ["TRAIN", "VALIDACION", "PANDEMIA_ANALIZAR_APARTE"], "TEST")
d["codigo_divipola"] = d["codigo_divipola"].astype(str)
cols = (["codigo_divipola", "municipio", "anio", "semana_epidemiologica", "semana_inicio", "semana_fin", "estado_calendario",
         "calendario_verificado_oficial", "regimen", "split_sugerido",
         "ira_0_4", "estado_dato_ira", "tiene_reportes_repetidos", "suma_difiere_de_ultimo", "ira_0_4_suma",
         "consultas_0_4_totales_ultimo_reporte", "proporcion_ira_sobre_consultas", "poblacion_0_4", "serie_dane", "cambio_de_serie",
         "tasa_ira_notificada_x1000_menores5",
         "ira_lag1", "ira_lag2", "ira_lag3", "ira_lag4", "ira_media_4s", "ira_media_8s", "ira_cambio_vs_lag1", "ira_52s_atras", "proporcion_ira_lag1"]
        + CL + [f"{v}_{s}" for v in CL for s in ("lag1", "lag2", "media_4s")]
        + ["semana_sin", "semana_cos", "mes_aprox",
           "objetivo_ira_t_mas_2", "objetivo_ira_t_mas_3", "objetivo_tasa_x1000_t_mas_2", "objetivo_tasa_x1000_t_mas_3",
           "semana_objetivo_t_mas_2", "semana_objetivo_t_mas_3",
           "fila_completa_h2", "fila_completa_h3", "tiene_temperatura_t", "tiene_humedad_t", "tiene_precipitacion_t",
           "variables_clima_disponibles_t", "mediana_ira_semanal_2012_2019_municipio", "municipio_volumen_ge10"])
d = d[cols]
d.to_csv(OUT / "dataset_entrenamiento.csv", index=False, encoding="utf-8-sig")

# ------------------------------ validaciones
V = []
def chk(nombre, ok, detalle=""):
    V.append(dict(validacion=nombre, resultado="OK" if ok else "FALLA", detalle=detalle))
chk("clave única (municipio, año, semana)", not d.duplicated(k).any(), f"{len(d)} filas")
chk("64 municipios x 574 semanas", len(d) == 64 * 574 and d.codigo_divipola.nunique() == 64)
chk("DIVIPOLA de los 64 municipios presentes en geográfico", set(d.codigo_divipola) == set(pd.read_csv(OUT / "dataset_geografico.csv", dtype=str).codigo_divipola))
chk("población presente en todas las filas", d.poblacion_0_4.notna().all())
chk("SIN_FILA no se convierte en 0", (d.loc[d.estado_dato_ira == "SIN_FILA", "ira_0_4"].isna()).all(), f"{int((d.estado_dato_ira=='SIN_FILA').sum())} municipio-semanas")
chk("sin valores negativos en IRA", (d.ira_0_4.dropna() >= 0).all())
# rezago: lag1 de la fila i es ira de la fila i-1 del mismo municipio
s = d.sample(500, random_state=1).index
prev = d.groupby("codigo_divipola")["ira_0_4"].shift(1)
chk("lag1 = ira de la semana anterior (muestra 500)", np.allclose(d.loc[s, "ira_lag1"].fillna(-1), prev.loc[s].fillna(-1)))
nxt = d.groupby("codigo_divipola")["ira_0_4"].shift(-2)
chk("objetivo t+2 = ira dos semanas después (muestra 500)", np.allclose(d.loc[s, "objetivo_ira_t_mas_2"].fillna(-1), nxt.loc[s].fillna(-1)))
chk("semana objetivo t+2 = semana_fin + 14 días", ((d["semana_objetivo_t_mas_2"] - d["semana_fin"]).dropna().dt.days == 14).all())
chk("semana objetivo t+3 = semana_fin + 21 días", ((d["semana_objetivo_t_mas_3"] - d["semana_fin"]).dropna().dt.days == 21).all())
chk("calendario continuo sin saltos", (cal.assign(f=pd.to_datetime(cal.semana_inicio)).f.diff().dropna().dt.days == 7).all())
chk("totales anuales 2019-2022 coinciden con SIVIGILA (54738/18476/23038/48415)",
    d.groupby("anio").ira_0_4.sum().loc[[2019, 2020, 2021, 2022]].astype(int).tolist() == [54738, 18476, 23038, 48415])
chk("clima solo en municipios aptos", all(d.loc[d[v].notna(), "codigo_divipola"].isin(set(sel[(sel.variable == v) & (sel.apta == True)].codigo_divipola)).all() for v in CL))
chk("no hay temperatura en Aldana (52022)", d.loc[d.codigo_divipola == "52022", ["temp_min", "temp_max", "temp_media"]].isna().all().all())
chk("humedad en rango 0-100", d.humedad_relativa.dropna().between(0, 100).all())
chk("precipitación >= 0", (d.precipitacion.dropna() >= 0).all())
pd.DataFrame(V).to_csv(OUT / "validaciones.csv", index=False, encoding="utf-8-sig")
print(pd.DataFrame(V).to_string(index=False))
print("filas completas h2:", int(d.fila_completa_h2.sum()), " h3:", int(d.fila_completa_h3.sum()))
r = d[d.fila_completa_h2]
print("completas h2 con precip:", int(r.tiene_precipitacion_t.sum()), " con temp:", int(r.tiene_temperatura_t.sum()), " con humedad:", int(r.tiene_humedad_t.sum()))
print(r.groupby("split_sugerido").size().to_dict(), "municipios con vol>=10:", int(d[d.municipio_volumen_ge10].codigo_divipola.nunique()))
print("columnas", len(cols))
