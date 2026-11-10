"""SIVIGILA evento 995 (IRA colectiva): lectura de XLSX y validación por fila.

Cada fila es un reporte colectivo, no un paciente. `NUM_CON` y la fila de origen se conservan; las repeticiones de
municipio-semana-prestador se marcan (`unresolved_repeat`) pero nunca se eliminan ni se suman (D-01).
"""

from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from app.importers.common import (
    SEVERITY_BLOCKING,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    ImporterError,
    Issue,
    ValidatedRow,
    is_blank,
    normalize_divipola,
    normalize_text,
    parse_date,
    parse_integer,
)
from app.models.integration import VALIDATION_MISSING, VALIDATION_PENDING, VALIDATION_REJECTED

EVENT_CODE = "995"
MIN_YEAR, MAX_YEAR = 2000, 2100

# Nombre canónico → alias aceptados (minúsculas). La lectura es por nombre de columna, nunca por posición,
# porque los libros de distintos años cambian de encabezados (D-07).
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "event_code": ("cod_eve",),
    "municipality_code": ("cod_mun", "cod_mun_"),
    "epi_year": ("año", "ano"),
    "epi_week": ("semana",),
    "provider_code": ("cod_pre",),
    "provider_subsite_code": ("cod_sub",),
    "report_consecutive": ("num_con",),
    "ira_ext_under1": ("iracext_1",),
    "ira_ext_age1": ("iracext_2",),
    "ira_ext_age2_4": ("iracext_3",),
    "notification_date": ("fec_not",),
}
REQUIRED_COLUMNS = (
    "event_code",
    "municipality_code",
    "epi_year",
    "epi_week",
    "provider_code",
    "report_consecutive",
    "ira_ext_under1",
    "ira_ext_age1",
    "ira_ext_age2_4",
)
COUNT_FIELDS = ("ira_ext_under1", "ira_ext_age1", "ira_ext_age2_4")


def resolve_columns(headers: Iterable[Any]) -> dict[str, int]:
    """Mapea nombres canónicos a posición usando los encabezados del libro; falla si falta alguna obligatoria."""
    normalized = [str(h or "").strip().lower() for h in headers]
    mapping: dict[str, int] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[canonical] = normalized.index(alias)
                break
    missing = [name for name in REQUIRED_COLUMNS if name not in mapping]
    if missing:
        raise ImporterError(f"SIVIGILA: faltan columnas obligatorias: {', '.join(missing)}")
    return mapping


def read_xlsx(path: Path, *, sheet_name: str, header_row: int = 1) -> Iterator[tuple[int, dict[str, Any]]]:
    """Itera (número de fila de Excel, valores por nombre canónico). Solo lectura; el libro no se modifica."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - dependencia declarada en requirements.txt
        raise ImporterError("Se requiere openpyxl para leer XLSX.") from exc

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            raise ImporterError(f"SIVIGILA: la hoja {sheet_name!r} no existe (hojas: {workbook.sheetnames})")
        sheet = workbook[sheet_name]
        rows = sheet.iter_rows(min_row=header_row, values_only=True)
        columns = resolve_columns(next(rows))
        for offset, values in enumerate(rows, start=header_row + 1):
            if all(is_blank(v) for v in values):
                continue
            yield offset, {name: (values[i] if i < len(values) else None) for name, i in columns.items()}
    finally:
        workbook.close()


def validate_row(
    raw: Mapping[str, Any],
    *,
    sheet_name: str,
    source_row_number: int,
    known_municipality_codes: frozenset[str] | None = None,
    years_with_53_weeks: frozenset[int] = frozenset(),
) -> ValidatedRow:
    row = ValidatedRow(sheet_name=sheet_name, source_row_number=source_row_number, record={})
    record = row.record

    event = normalize_text(raw.get("event_code"))
    record["event_code"] = event
    if event != EVENT_CODE:
        row.add(Issue("event_code_unexpected", SEVERITY_BLOCKING, f"Evento {event!r}; se esperaba {EVENT_CODE}", "event_code"), status=VALIDATION_REJECTED)

    code = normalize_divipola(raw.get("municipality_code"))
    record["municipality_code"] = code
    if code is None:
        row.add(Issue("municipality_code_invalid", SEVERITY_BLOCKING, "Código DIVIPOLA ausente o con formato inválido", "municipality_code"), status=VALIDATION_REJECTED)
    elif known_municipality_codes is not None and code not in known_municipality_codes:
        row.add(Issue("municipality_unknown", SEVERITY_BLOCKING, f"DIVIPOLA {code} no existe en el catálogo", "municipality_code"), status=VALIDATION_REJECTED)

    year = _int_field(row, raw, "epi_year")
    if year is not None and not MIN_YEAR <= year <= MAX_YEAR:
        row.add(Issue("year_out_of_range", SEVERITY_BLOCKING, f"Año {year} fuera de {MIN_YEAR}-{MAX_YEAR}", "epi_year"), status=VALIDATION_REJECTED)
        year = None
    record["epi_year"] = year
    week = _int_field(row, raw, "epi_week")
    if week is not None and not 1 <= week <= 53:
        row.add(Issue("week_out_of_range", SEVERITY_BLOCKING, f"Semana {week} fuera de 1-53", "epi_week"), status=VALIDATION_REJECTED)
        week = None
    elif week == 53 and year not in years_with_53_weeks:
        # El calendario epidemiológico por año aún no está verificado (D-11): la semana 53 no se descarta ni se acepta.
        row.add(Issue("week_53_calendar_unverified", SEVERITY_WARNING, "Semana 53 sin calendario oficial verificado para el año", "epi_week"), status=VALIDATION_PENDING)
    record["epi_week"] = week

    for name in COUNT_FIELDS:
        record[name] = _count_field(row, raw, name)
    present = [record[name] for name in COUNT_FIELDS if record[name] is not None]
    if not present and row.status != VALIDATION_REJECTED:
        row.add(Issue("all_counts_missing", SEVERITY_WARNING, "Los tres conteos IRACEXT están vacíos; no se asume cero"), status=VALIDATION_MISSING)
    elif len(present) < len(COUNT_FIELDS) and row.status != VALIDATION_REJECTED:
        row.add(Issue("partial_counts_missing", SEVERITY_WARNING, "Algún conteo IRACEXT está vacío; no se asume cero"), status=VALIDATION_PENDING)

    try:
        record["notification_date"] = parse_date(raw.get("notification_date"))
    except ValueError:
        record["notification_date"] = None
        row.add(Issue("notification_date_invalid", SEVERITY_WARNING, "Fecha de notificación no interpretable; se omite", "notification_date"))

    record["provider_code"] = normalize_text(raw.get("provider_code"))
    record["provider_subsite_code"] = normalize_text(raw.get("provider_subsite_code"))
    record["report_consecutive"] = normalize_text(raw.get("report_consecutive"))
    record["report_group_status"] = "unreviewed"
    return row


def _int_field(row: ValidatedRow, raw: Mapping[str, Any], name: str) -> int | None:
    value = raw.get(name)
    if is_blank(value):
        row.add(Issue(f"{name}_missing", SEVERITY_BLOCKING, f"{name} vacío", name), status=VALIDATION_REJECTED)
        return None
    try:
        return parse_integer(value)
    except ValueError:
        row.add(Issue(f"{name}_not_integer", SEVERITY_BLOCKING, f"{name}={value!r} no es un entero", name), status=VALIDATION_REJECTED)
        return None


def _count_field(row: ValidatedRow, raw: Mapping[str, Any], name: str) -> int | None:
    value = raw.get(name)
    if is_blank(value):
        return None  # ausente ≠ 0: queda NULL
    try:
        number = parse_integer(value)
    except ValueError:
        row.add(Issue(f"{name}_not_integer", SEVERITY_BLOCKING, f"{name}={value!r} no es un entero", name), status=VALIDATION_REJECTED)
        return None
    if number < 0:
        row.add(Issue(f"{name}_negative", SEVERITY_BLOCKING, f"{name}={number} es negativo", name), status=VALIDATION_REJECTED)
        return None
    return number


def flag_repeats(rows: list[ValidatedRow]) -> int:
    """Marca grupos con varios reportes del mismo municipio-año-semana-prestador-sede-evento.

    Solo anota `report_group_status`; no elimina, suma ni elige entre filas. Devuelve el número de grupos repetidos.
    """
    groups: dict[tuple, list[ValidatedRow]] = defaultdict(list)
    for row in rows:
        rec = row.record
        key = tuple(rec.get(k) for k in ("municipality_code", "epi_year", "epi_week", "provider_code", "provider_subsite_code", "event_code"))
        if None in key[:3] or key[3] is None:
            continue  # sin clave completa no se puede afirmar nada sobre repetición
        groups[key].append(row)
    repeated = 0
    for members in groups.values():
        if len(members) == 1:
            members[0].record["report_group_status"] = "single_report"
            continue
        repeated += 1
        for member in members:
            member.record["report_group_status"] = "unresolved_repeat"
            member.add(Issue("repeated_provider_week", SEVERITY_INFO, f"{len(members)} reportes para el mismo prestador-semana; relación sin resolver (D-01)"))
    return repeated
