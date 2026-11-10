"""RESPIRA v2 / paso 5. dataset_poblacional: población DANE 0-4 años por municipio y año (2012-2022), área 'Total'.
Dos series DANE distintas (proyección 2005-2017 hasta 2017; proyección 2018-2042 desde 2018). No se empalma ni se ajusta:
se conserva la serie de origen y se marca el cambio de serie y la variación interanual."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2"
geo = pd.read_csv(OUT / "dataset_geografico.csv", dtype={"codigo_divipola": str})
fr = []
for t in "ab":
    d = pd.read_csv(ROOT / "data" / "interim" / f"dane_narino_{t}.csv", dtype=str)
    fr.append(d)
d = pd.concat(fr, ignore_index=True)
d = d[d["area"] == "Total"].copy()
for c in [c for c in d.columns if c.split("_")[0] in ("hombres", "mujeres", "total")]:
    d[c] = pd.to_numeric(d[c])
d["anio"] = d["anio"].astype(int)
d = d[(d.anio >= 2012) & (d.anio <= 2022)]
assert not d.duplicated(["mpio", "anio"]).any()
out = pd.DataFrame({"codigo_divipola": d["mpio"], "anio": d["anio"], "serie_dane": d["dane_libro"]})
for i in range(5):
    out[f"poblacion_{i}_anios"] = d[f"total_{i}"].values
out["poblacion_0_4"] = out[[f"poblacion_{i}_anios" for i in range(5)]].sum(axis=1)
chk = (d[[f"hombres_{i}" for i in range(5)]].values + d[[f"mujeres_{i}" for i in range(5)]].values
       == d[[f"total_{i}" for i in range(5)]].values).all(axis=1)
out["control_total_igual_hombres_mas_mujeres"] = chk
out = out.merge(geo[["codigo_divipola", "municipio"]], on="codigo_divipola", how="right").sort_values(["codigo_divipola", "anio"])
out["variacion_interanual_pct"] = out.groupby("codigo_divipola")["poblacion_0_4"].pct_change().mul(100).round(2)
out["cambio_de_serie"] = out["anio"].eq(2018)
out["fuente"] = "DANE proyecciones municipales por área, sexo y edad simple"
out = out[["codigo_divipola", "municipio", "anio", "serie_dane", "poblacion_0_anios", "poblacion_1_anios", "poblacion_2_anios",
           "poblacion_3_anios", "poblacion_4_anios", "poblacion_0_4", "variacion_interanual_pct", "cambio_de_serie",
           "control_total_igual_hombres_mas_mujeres", "fuente"]]
assert len(out) == 704 and out.poblacion_0_4.notna().all()
out.to_csv(OUT / "dataset_poblacional.csv", index=False, encoding="utf-8-sig")
j = out[out.anio == 2018]["variacion_interanual_pct"]
print("filas", len(out), "control OK", bool(out.control_total_igual_hombres_mas_mujeres.all()),
      "salto 2017->2018 mediana %.1f%%, min %.1f, max %.1f" % (j.median(), j.min(), j.max()))
print("menores de 5 en 2022: min", out[out.anio == 2022].poblacion_0_4.min(), "total Nariño", out[out.anio == 2022].poblacion_0_4.sum())
