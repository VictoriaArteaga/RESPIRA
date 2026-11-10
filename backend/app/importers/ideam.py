"""IDEAM: lectura de archivos `.data` (`Fecha|Valor`) y validación por observación diaria.

Solo se registran observaciones; ningún agregado semanal se calcula aquí. Las variables cuya semántica o unidad no
está confirmada (D-04, D-05) se aceptan como `pending`, nunca como `valid`. No se aplican rangos de plausibilidad
porque no existen referencias oficiales adoptadas todavía.
"""

import re
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.importers.common import (
    SEVERITY_BLOCKING,
    SEVERITY_WARNING,
    ImporterError,
    Issue,
    ValidatedRow,
    is_blank,
    normalize_text,
    parse_date,
)
from app.models.integration import VALIDATION_MISSING, VALIDATION_PENDING, VALIDATION_REJECTED

FILENAME_PATTERN = re.compile(r"^(?P<variable>[A-Z0-9_]+)@(?P<station>\d+)\.data$")


@dataclass(frozen=True)
class VariableSpec:
    unit: str | None
    confirmed: bool  # False → semántica/unidad pendiente de confirmación IDEAM
    non_negative: bool = False


VARIABLES: dict[str, VariableSpec] = {
    # Temperatura del aire diaria (mínima, máxima, media): documentadas en el manual IDEAM GDI-M005.
    "TSSM_MN_D": VariableSpec("°C", True),
    "TSSM_MX_D": VariableSpec("°C", True),
    "TSSM_MEDIA_D": VariableSpec("°C", True),
    # Reconocidas pero con semántica/unidad no confirmada (D-05): quedan pendientes.
    "TSSM_CON": VariableSpec(None, False),
    "PTPM_CON_INTER": VariableSpec(None, False, non_negative=True),
    "HR_CAL_MEDIA_D": VariableSpec(None, False, non_negative=True),
    "TPR_CAL": VariableSpec(None, False),
    "TV_CAL": VariableSpec(None, False),
}


def parse_filename(path: Path) -> tuple[str, str]:
    match = FILENAME_PATTERN.match(path.name)
    if not match:
        raise ImporterError(f"IDEAM: nombre de archivo no reconocido: {path.name!r} (se espera VARIABLE@ESTACION.data)")
    return match["variable"], match["station"]


def read_data_file(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Itera (número de línea, {'date','value'}) como texto original. Exige la cabecera exacta `Fecha|Valor`."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        header = handle.readline().strip()
        if header != "Fecha|Valor":
            raise ImporterError(f"IDEAM: cabecera inesperada {header!r} en {path.name}")
        for number, line in enumerate(handle, start=2):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            date_text, sep, value_text = line.partition("|")
            if not sep:
                yield number, {"date": line, "value": None, "malformed": True}
            else:
                yield number, {"date": date_text, "value": value_text}


def validate_observation(
    raw: Mapping[str, Any],
    *,
    station_code: str,
    variable_code: str,
    source_row_number: int,
    known_station_codes: frozenset[str] | None = None,
    today: date | None = None,
) -> ValidatedRow:
    row = ValidatedRow(sheet_name="", source_row_number=source_row_number, record={})
    record = row.record
    station = normalize_text(station_code)
    record.update({"station_code_source": station, "variable_code": variable_code})

    if station is None or not station.isdigit():
        row.add(Issue("station_code_invalid", SEVERITY_BLOCKING, "Código de estación ausente o no numérico", "station"), status=VALIDATION_REJECTED)
    elif known_station_codes is not None and station not in known_station_codes:
        row.add(Issue("station_unknown", SEVERITY_BLOCKING, f"Estación {station} no existe en el catálogo", "station"), status=VALIDATION_REJECTED)

    spec = VARIABLES.get(variable_code)
    if spec is None:
        row.add(Issue("variable_unrecognized", SEVERITY_BLOCKING, f"Variable {variable_code!r} no reconocida", "variable"), status=VALIDATION_REJECTED)
    else:
        record["unit_original"] = spec.unit
        if not spec.confirmed:
            row.add(Issue("variable_semantics_pending", SEVERITY_WARNING, f"{variable_code}: semántica/unidad sin confirmar (D-05)", "variable"), status=VALIDATION_PENDING)

    try:
        observed = None if raw.get("malformed") else parse_date(raw.get("date"))
        if observed is None:
            raise ValueError("empty")
    except ValueError:
        observed = None
        row.add(Issue("date_invalid", SEVERITY_BLOCKING, f"Fecha no interpretable: {raw.get('date')!r}", "date"), status=VALIDATION_REJECTED)
    else:
        if observed > (today or date.today()):
            row.add(Issue("date_in_future", SEVERITY_BLOCKING, f"Fecha futura {observed}", "date"), status=VALIDATION_REJECTED)
    record["observed_date"] = observed

    value_text = raw.get("value")
    record["value_text_original"] = None if value_text is None else str(value_text).strip()[:60]
    record["value_numeric"] = None
    if is_blank(value_text):
        # Valor ausente: queda NULL, nunca 0 (el cero solo existe si la fuente lo trae).
        row.add(Issue("value_missing", SEVERITY_WARNING, "Valor ausente", "value"), status=VALIDATION_MISSING)
    else:
        try:
            number = float(str(value_text).strip().replace(",", "."))
            if number != number or number in (float("inf"), float("-inf")):
                raise ValueError("not finite")
        except ValueError:
            row.add(Issue("value_not_numeric", SEVERITY_BLOCKING, f"Valor no numérico: {value_text!r}", "value"), status=VALIDATION_REJECTED)
        else:
            if spec is not None and spec.non_negative and number < 0:
                row.add(Issue("value_negative", SEVERITY_BLOCKING, f"{variable_code} no admite negativos: {number}", "value"), status=VALIDATION_REJECTED)
            else:
                record["value_numeric"] = number
    return row


def flag_duplicate_dates(rows: list[ValidatedRow]) -> int:
    """Marca fechas repetidas dentro de una misma estación-variable como pendientes; no elimina ninguna."""
    counts = Counter((r.record["station_code_source"], r.record["variable_code"], r.record["observed_date"]) for r in rows if r.record["observed_date"])
    duplicated = 0
    for row in rows:
        key = (row.record["station_code_source"], row.record["variable_code"], row.record["observed_date"])
        if row.record["observed_date"] and counts[key] > 1:
            duplicated += 1
            row.add(Issue("duplicate_observation_date", SEVERITY_WARNING, "Fecha repetida para la misma estación y variable", "date"), status=VALIDATION_PENDING)
    return duplicated


def temporal_coverage(dates: Iterable[date], start: date, end: date) -> dict[str, Any]:
    """Cobertura de días presentes en [start, end]. Informa huecos; no los rellena."""
    if end < start:
        raise ValueError("end must not precede start")
    present = {d for d in dates if start <= d <= end}
    expected = (end - start).days + 1
    first_missing = next((start + timedelta(days=i) for i in range(expected) if start + timedelta(days=i) not in present), None)
    return {
        "expected_days": expected,
        "observed_days": len(present),
        "missing_days": expected - len(present),
        "coverage_pct": round(100 * len(present) / expected, 2),
        "first_missing_date": first_missing.isoformat() if first_missing else None,
    }
