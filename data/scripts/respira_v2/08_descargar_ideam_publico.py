"""RESPIRA v2 / paso 8. Descarga PÚBLICA de IDEAM desde datos.gov.co (Socrata), estaciones de Nariño, 2022-2025.
Se agrega a diario en el servidor (mín, máx, media, suma y nº de lecturas por estación-sensor-día) para no bajar millones de lecturas.
Conjuntos: sbwg-7ju4 (Temperatura Ambiente del Aire), s54a-sgyg (Precipitación), uext-mhny (Humedad del Aire).
Salida: data/respira_v2/fuentes_oficiales/ideam_publico_diario_{variable}.csv + ideam_publico_manifest.json (procedencia).
2022 se incluye solo para comprobar el empalme con la serie histórica (.data) usada hasta 2022."""
import csv, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import urllib.parse, urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "respira_v2" / "fuentes_oficiales"
DATASETS = {"temperatura": "sbwg-7ju4", "precipitacion": "s54a-sgyg", "humedad": "uext-mhny"}
MONTHS = [(y, m) for y in range(2022, 2026) for m in range(1, 13)]
SELECT = ("codigoestacion,codigosensor,nombreestacion,municipio,descripcionsensor,unidadmedida,date_trunc_ymd(fechaobservacion) as dia,"
          "min(valorobservado) as vmin,max(valorobservado) as vmax,avg(valorobservado) as vmed,sum(valorobservado) as vsuma,count(*) as n")
GROUP = "codigoestacion,codigosensor,nombreestacion,municipio,descripcionsensor,unidadmedida,dia"
FIELDS = ["codigoestacion", "codigosensor", "nombreestacion", "municipio", "descripcionsensor", "unidadmedida", "dia", "vmin", "vmax", "vmed", "vsuma", "n"]


def fetch(dataset: str, start: str, end: str, offset: int = 0) -> list[dict]:
    params = {"$select": SELECT, "$group": GROUP, "$limit": "50000", "$offset": str(offset), "$order": "dia",
              "$where": f"departamento like 'NARI%' AND fechaobservacion >= '{start}T00:00:00' AND fechaobservacion < '{end}T00:00:00'"}
    url = f"https://www.datos.gov.co/resource/{dataset}.json?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "respira-academico/1.0"}), timeout=240) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as error:   # reintento con espera creciente
            print("  reintento", attempt + 1, type(error).__name__, flush=True)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"fallo definitivo {dataset} {start}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "portal": "https://www.datos.gov.co",
                "licencia_portal": "datos abiertos IDEAM (ver ficha de cada conjunto)", "conjuntos": {}}
    for var, ds in DATASETS.items():
        rows_total, per_month = 0, {}
        with open(OUT / f"ideam_publico_diario_{var}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            for y, m in MONTHS:
                start = f"{y}-{m:02d}-01"
                end = f"{y + (m == 12)}-{(m % 12) + 1:02d}-01"
                offset, got = 0, 0
                while True:
                    part = fetch(ds, start, end, offset)
                    for r in part:
                        w.writerow(r)
                    got += len(part)
                    if len(part) < 50000:
                        break
                    offset += 50000
                per_month[f"{y}-{m:02d}"] = got
                rows_total += got
                print(var, y, m, got, flush=True)
                time.sleep(0.6)
        manifest["conjuntos"][var] = {"id": ds, "url": f"https://www.datos.gov.co/resource/{ds}.json", "filas_diarias": rows_total, "por_mes": per_month}
    (OUT / "ideam_publico_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("listo", {k: v["filas_diarias"] for k, v in manifest["conjuntos"].items()})
