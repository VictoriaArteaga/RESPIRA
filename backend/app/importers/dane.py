"""DANE: validación de población anual proyectada por municipio.

Cada libro DANE tiene un diseño distinto (2005-2017 y 2018-2042). La lectura de cada libro requiere un mapa de
encabezados revisado contra el libro real y queda pendiente hasta la fase de importación; aquí se valida el contrato
normalizado (una fila por municipio-año-área-edad-sexo) que ese lector deberá producir.
"""

from collections.abc import Mapping
from typing import Any

from app.importers.common import (
    SEVERITY_BLOCKING,
    SEVERITY_WARNING,
    Issue,
    ValidatedRow,
    is_blank,
    normalize_divipola,
    normalize_text,
    parse_integer,
)
from app.models.integration import VALIDATION_MISSING, VALIDATION_REJECTED

DEPARTMENT_PREFIX = "52"  # Nariño
MIN_YEAR, MAX_YEAR = 2005, 2042  # cobertura de las proyecciones DANE disponibles
EXPECTED_AGE_RANGE = (0, 4)


def validate_population_row(
    raw: Mapping[str, Any],
    *,
    source_row_number: int,
    sheet_name: str = "",
    known_municipality_codes: frozenset[str] | None = None,
    expected_age_range: tuple[int, int] = EXPECTED_AGE_RANGE,
) -> ValidatedRow:
    row = ValidatedRow(sheet_name=sheet_name, source_row_number=source_row_number, record={})
    record = row.record

    code = normalize_divipola(raw.get("municipality_code"))
    record["municipality_code"] = code
    if code is None:
        row.add(Issue("divipola_invalid", SEVERITY_BLOCKING, "DIVIPOLA ausente o con formato inválido", "municipality_code"), status=VALIDATION_REJECTED)
    elif not code.startswith(DEPARTMENT_PREFIX):
        row.add(Issue("divipola_outside_department", SEVERITY_BLOCKING, f"{code} no pertenece al departamento {DEPARTMENT_PREFIX}", "municipality_code"), status=VALIDATION_REJECTED)
    elif known_municipality_codes is not None and code not in known_municipality_codes:
        row.add(Issue("municipality_unknown", SEVERITY_BLOCKING, f"DIVIPOLA {code} no existe en el catálogo", "municipality_code"), status=VALIDATION_REJECTED)

    year = _int(row, raw, "reference_year", required=True)
    if year is not None and not MIN_YEAR <= year <= MAX_YEAR:
        row.add(Issue("year_out_of_range", SEVERITY_BLOCKING, f"Año {year} fuera de {MIN_YEAR}-{MAX_YEAR}", "reference_year"), status=VALIDATION_REJECTED)
        year = None
    record["reference_year"] = year

    age_min = _int(row, raw, "age_min", required=True)
    age_max = _int(row, raw, "age_max", required=True)
    record["age_min"], record["age_max"] = age_min, age_max
    if age_min is not None and age_max is not None and (age_min, age_max) != expected_age_range:
        row.add(Issue("age_group_unexpected", SEVERITY_BLOCKING, f"Grupo {age_min}-{age_max}; se esperaba {expected_age_range[0]}-{expected_age_range[1]}", "age_min"), status=VALIDATION_REJECTED)

    record["population_area"] = normalize_text(raw.get("population_area"))
    record["sex_code"] = normalize_text(raw.get("sex_code"))
    record["workbook_version"] = normalize_text(raw.get("workbook_version"))
    for name in ("population_area", "sex_code"):
        if record[name] is None:
            row.add(Issue(f"{name}_missing", SEVERITY_BLOCKING, f"{name} vacío", name), status=VALIDATION_REJECTED)

    count = raw.get("population_count")
    record["population_count"] = None
    if is_blank(count):
        row.add(Issue("population_missing", SEVERITY_WARNING, "Población ausente; no se asume cero", "population_count"), status=VALIDATION_MISSING)
    else:
        try:
            number = parse_integer(count)
        except ValueError:
            row.add(Issue("population_not_integer", SEVERITY_BLOCKING, f"Población {count!r} no es un entero", "population_count"), status=VALIDATION_REJECTED)
        else:
            if number < 0:
                row.add(Issue("population_negative", SEVERITY_BLOCKING, f"Población negativa: {number}", "population_count"), status=VALIDATION_REJECTED)
            else:
                record["population_count"] = number
    return row


def _int(row: ValidatedRow, raw: Mapping[str, Any], name: str, *, required: bool) -> int | None:
    value = raw.get(name)
    if is_blank(value):
        if required:
            row.add(Issue(f"{name}_missing", SEVERITY_BLOCKING, f"{name} vacío", name), status=VALIDATION_REJECTED)
        return None
    try:
        return parse_integer(value)
    except ValueError:
        row.add(Issue(f"{name}_not_integer", SEVERITY_BLOCKING, f"{name}={value!r} no es un entero", name), status=VALIDATION_REJECTED)
        return None
