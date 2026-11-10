"""RESPIRA v2 / paso 10. Exporta las atenciones por IRA REALES (SIVIGILA 995, <5 años, 2012-2022) para la interfaz.

Lee data/respira_v2/dataset_epidemiologico.csv y dataset_geografico.csv y escribe frontend/src/mocks/real-data.json
(unos 150 KB). La interfaz lo muestra junto a los datos simulados de demostración.
Regla: una semana sin dato (SIN_FILA, vacío en la fuente) se exporta como null y la interfaz NO la dibuja; nunca se convierte en cero."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "respira_v2"
OUT = ROOT / "frontend" / "src" / "mocks" / "real-data.json"
PARTICULAS = {"de", "del", "la", "las", "los", "el", "y"}


def nombre_legible(texto: str) -> str:
    """'SAN ANDRÉS DE TUMACO' -> 'San Andrés de Tumaco' (las partículas quedan en minúscula salvo al inicio)."""
    palabras = texto.lower().split()
    return " ".join(p if (i > 0 and p in PARTICULAS) else p.capitalize() for i, p in enumerate(palabras))


with open(DATA / "dataset_geografico.csv", encoding="utf-8-sig", newline="") as fh:
    geo = {r["codigo_divipola"]: r for r in csv.DictReader(fh)}

semanas: list[tuple[int, int]] = []
valores: dict[str, dict[tuple[int, int], int | None]] = {c: {} for c in geo}
with open(DATA / "dataset_epidemiologico.csv", encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        clave = (int(r["anio"]), int(r["semana_epidemiologica"]))
        if clave not in semanas:
            semanas.append(clave)
        v = r["ira_0_4"]
        valores[r["codigo_divipola"]][clave] = round(float(v)) if v not in ("", "nan") else None
semanas.sort()

municipios = []
for codigo in sorted(geo):
    g = geo[codigo]
    municipios.append({"c": codigo, "n": nombre_legible(g["municipio"]), "lat": round(float(g["latitud_cabecera"]), 5),
                       "lon": round(float(g["longitud_cabecera"]), 5), "v": [valores[codigo].get(s) for s in semanas]})

assert len(municipios) == 64 and len(semanas) == 574
con_dato = sum(1 for m in municipios for v in m["v"] if v is not None)
OUT.write_text(json.dumps({
    "fuente": "SIVIGILA evento 995 (atenciones por IRA notificadas, menores de 5 años); DIVIPOLA DANE",
    "periodo": "2012-2022", "semanas": semanas, "municipios": municipios}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"{OUT.name}: {len(municipios)} municipios, {len(semanas)} semanas, {con_dato} semanas con dato "
      f"({len(municipios) * len(semanas) - con_dato} sin dato, no se dibujan), {OUT.stat().st_size / 1024:.0f} KB")
print([m["n"] for m in municipios if " de " in m["n"] or m["n"].startswith(("El ", "La ", "Los "))][:8])
