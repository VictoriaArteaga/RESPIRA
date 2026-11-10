"""RESPIRA v2 / paso 2. dataset_geografico (DIVIPOLA oficial DANE vía datos.gov.co, recurso gdxc-w37w, corte 30-dic-2024)
y tabla estación->municipio con distancia calculada a la cabecera. Sin altitud municipal (no hay fuente oficial
cargada): queda vacía. Las coordenadas DIVIPOLA son de la cabecera/capital del municipio, no centroides."""
import json, math, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "data" / "scripts" / "pipeline"))
from respira_datasets.ideam import nz, MANUAL_NAME_MAP, read_csv_any
OUT = ROOT / "data" / "respira_v2"
raw = json.load(open(OUT / "fuentes_oficiales" / "divipola_narino_datosgovco_gdxc-w37w.json", encoding="utf-8"))
g = pd.DataFrame(raw)
g["latitud"] = g["latitud"].str.replace(",", ".").astype(float)
g["longitud"] = g["longitud"].str.replace(",", ".").astype(float)
geo = pd.DataFrame({"codigo_divipola": g["cod_mpio"], "municipio": g["nom_mpio"], "codigo_departamento": g["cod_dpto"],
                    "departamento": g["dpto"], "latitud_cabecera": g["latitud"], "longitud_cabecera": g["longitud"],
                    "altitud_cabecera_m": pd.NA,
                    "fuente_coordenadas": "DANE DIVIPOLA (datos.gov.co gdxc-w37w, corte 2024-12-30); coordenada de cabecera, no centroide",
                    "fuente_altitud": "NO DISPONIBLE (pendiente de fuente oficial)"}).sort_values("codigo_divipola")
assert len(geo) == 64 and geo.codigo_divipola.is_unique
geo.to_csv(OUT / "dataset_geografico.csv", index=False, encoding="utf-8-sig")

st = read_csv_any(ROOT / "reports" / "estaciones_candidatas_ideam.csv")
dn = {nz(r.municipio): r.codigo_divipola for r in geo.itertuples()}
st["codigo_divipola_catalogo"] = st["municipio"].map(lambda m: dn.get(nz(m)) or MANUAL_NAME_MAP.get(nz(m)))
lat = {r.codigo_divipola: (r.latitud_cabecera, r.longitud_cabecera) for r in geo.itertuples()}
def hav(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0]); dl = math.radians(b[1] - a[1]); dp = p2 - p1
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))
def d(r):
    c = r.codigo_divipola_catalogo
    if pd.isna(c) or pd.isna(r.latitud) or pd.isna(r.longitud): return None
    return round(hav((float(r.latitud), float(r.longitud)), lat[c]), 2)
st["distancia_a_cabecera_km"] = st.apply(d, axis=1)
# municipio de cabecera más cercano a la estación (control del código por nombre del catálogo)
def nearest(r):
    if pd.isna(r.latitud) or pd.isna(r.longitud): return None
    return min(lat, key=lambda c: hav((float(r.latitud), float(r.longitud)), lat[c]))
st["divipola_cabecera_mas_cercana"] = st.apply(nearest, axis=1)
st["coincide_catalogo_y_cercania"] = st["codigo_divipola_catalogo"] == st["divipola_cabecera_mas_cercana"]
cols = ["codigo_estacion", "nombre_estacion", "municipio", "codigo_divipola_catalogo", "latitud", "longitud", "altitud",
        "estado_catalogo", "distancia_a_cabecera_km", "divipola_cabecera_mas_cercana", "coincide_catalogo_y_cercania"]
st[cols].rename(columns={"municipio": "municipio_catalogo_ideam", "altitud": "altitud_estacion_m"}).to_csv(
    OUT / "estacion_municipio.csv", index=False, encoding="utf-8-sig")
print("sin DIVIPOLA por catálogo:", st[st.codigo_divipola_catalogo.isna()][["codigo_estacion", "municipio"]].values.tolist())
print(st["coincide_catalogo_y_cercania"].value_counts().to_dict(), "dist mediana", st.distancia_a_cabecera_km.median(), "max", st.distancia_a_cabecera_km.max())
