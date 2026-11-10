"""Valida un archivo fuente SIN escribir en ninguna base de datos y emite un resumen JSON.

    python scripts/validate_source.py sivigila RUTA.xlsx --sheet Hoja1 [--header-row 1]
    python scripts/validate_source.py ideam RUTA/TSSM_MN_D@52045020.data

Solo lectura: no abre conexión, no modifica el archivo y no importa nada. Los rechazos y las advertencias se
cuentan por código; use --max-examples para ver filas concretas.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# validate_source no necesita base de datos, pero importar app.* carga Settings; se dan valores inertes si faltan.
import os  # noqa: E402

for _key, _value in {"DB_HOST": "unused", "DB_NAME": "unused", "DB_USER": "unused", "DB_PASSWORD": "unused", "JWT_SECRET_KEY": "x" * 32}.items():
    os.environ.setdefault(_key, _value)

from app.importers import ideam, sivigila  # noqa: E402
from app.importers.common import TRANSFORMATION_VERSION, file_sha256, summarize  # noqa: E402


def _report(path: Path, rows: list, extra: dict, max_examples: int) -> dict:
    examples = [
        {"row": r.source_row_number, "status": r.status, "issues": [i.code for i in r.issues]}
        for r in rows
        if r.status != "valid"
    ][:max_examples]
    return {
        "file": path.name,
        "sha256": file_sha256(path),
        "transformation_version": TRANSFORMATION_VERSION,
        **summarize(rows),
        **extra,
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="source", required=True)
    siv = sub.add_parser("sivigila")
    siv.add_argument("path", type=Path)
    siv.add_argument("--sheet", required=True)
    siv.add_argument("--header-row", type=int, default=1)
    ide = sub.add_parser("ideam")
    ide.add_argument("path", type=Path)
    parser.add_argument("--max-examples", type=int, default=10)
    args = parser.parse_args()

    if args.source == "sivigila":
        rows = [
            sivigila.validate_row(raw, sheet_name=args.sheet, source_row_number=number)
            for number, raw in sivigila.read_xlsx(args.path, sheet_name=args.sheet, header_row=args.header_row)
        ]
        extra = {"repeated_groups": sivigila.flag_repeats(rows)}
    else:
        variable, station = ideam.parse_filename(args.path)
        rows = [
            ideam.validate_observation(raw, station_code=station, variable_code=variable, source_row_number=number)
            for number, raw in ideam.read_data_file(args.path)
        ]
        dates = [r.record["observed_date"] for r in rows if r.record["observed_date"]]
        extra = {"duplicate_dates": ideam.flag_duplicate_dates(rows)}
        if dates:
            extra["coverage"] = ideam.temporal_coverage(dates, min(dates), max(dates))
    print(json.dumps(_report(args.path, rows, extra, args.max_examples), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
