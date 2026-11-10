"""Tipos y utilidades compartidas por los lectores y validadores de fuentes.

Los validadores son funciones puras: reciben una fila ya leída y devuelven un `ValidatedRow`. Nunca corrigen,
imputan ni descartan valores; un dato dudoso se conserva con su estado y los hallazgos que lo explican.
"""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.models.integration import (
    VALIDATION_MISSING,
    VALIDATION_PENDING,
    VALIDATION_REJECTED,
    VALIDATION_VALID,
)

# Se incrementa cuando cambian las reglas de lectura/validación; queda registrada en cada lote.
TRANSFORMATION_VERSION = "2.2.0"

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_BLOCKING = "blocking"

_BLANK_TOKENS = {"", "na", "n/a", "nan", "null", "none", "nd", "s/d"}
_DIVIPOLA = re.compile(r"^\d{5}$")


class ImporterError(Exception):
    """El archivo no tiene la estructura esperada; el lote completo debe rechazarse."""


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    message: str
    field: str | None = None


@dataclass
class ValidatedRow:
    sheet_name: str
    source_row_number: int
    record: dict[str, Any]
    status: str = VALIDATION_VALID
    issues: list[Issue] = field(default_factory=list)

    def add(self, issue: Issue, *, status: str | None = None) -> None:
        """Registra un hallazgo y, si se indica, degrada el estado (rejected > missing > pending > valid)."""
        self.issues.append(issue)
        if status is not None:
            self.status = worst_status(self.status, status)


_STATUS_RANK = {VALIDATION_VALID: 0, VALIDATION_PENDING: 1, VALIDATION_MISSING: 2, VALIDATION_REJECTED: 3}


def worst_status(current: str, candidate: str) -> str:
    return candidate if _STATUS_RANK[candidate] > _STATUS_RANK[current] else current


def is_blank(value: Any) -> bool:
    """Celda vacía o token explícito de ausencia. El cero NO es un valor en blanco."""
    if value is None:
        return True
    return isinstance(value, str) and value.strip().lower() in _BLANK_TOKENS


def normalize_text(value: Any) -> str | None:
    if is_blank(value):
        return None
    text = str(value).strip()
    # Excel entrega códigos numéricos como 52240.0; solo se recorta el sufijo ".0" exacto.
    return text[:-2] if re.fullmatch(r"\d+\.0", text) else text


def normalize_divipola(value: Any) -> str | None:
    """Devuelve el código DIVIPOLA como texto de 5 dígitos conservando ceros, o None si no es interpretable."""
    text = normalize_text(value)
    if text is None or not text.isdigit() or len(text) > 5:
        return None
    text = text.zfill(5)
    return text if _DIVIPOLA.match(text) else None


def parse_integer(value: Any) -> int | None:
    """Entero estricto: 3, '3' y 3.0 son válidos; 3.5, 'abc' y los booleanos lanzan ValueError."""
    if isinstance(value, bool):
        raise ValueError("boolean is not an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")) or not value.is_integer():
            raise ValueError("not an integer")
        return int(value)
    text = str(value).strip().replace(",", ".")
    number = float(text)
    if not number.is_integer():
        raise ValueError("not an integer")
    return int(number)


def parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = normalize_text(value)
    if text is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognized date {text!r}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize(rows: list[ValidatedRow]) -> dict[str, Any]:
    """Resumen estable para informes de validación (conteo por estado y por código de hallazgo)."""
    by_status: dict[str, int] = {}
    by_issue: dict[str, int] = {}
    for row in rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1
        for issue in row.issues:
            by_issue[issue.code] = by_issue.get(issue.code, 0) + 1
    return {"rows": len(rows), "by_status": by_status, "by_issue": dict(sorted(by_issue.items()))}
