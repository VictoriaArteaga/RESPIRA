"""Persistencia de filas validadas con trazabilidad (fuente → lote → fila de origen → hallazgos).

El cargador NO hace commit: quien lo invoca controla la transacción (y puede hacer rollback). Nada en el flujo de
la aplicación lo ejecuta; la importación de datos oficiales requiere autorización explícita y una ejecución manual.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.importers.common import (
    SEVERITY_WARNING,
    TRANSFORMATION_VERSION,
    Issue,
    ValidatedRow,
)
from app.models.integration import (
    VALIDATION_PENDING,
    VALIDATION_REJECTED,
    VALIDATION_VALID,
    AnnualPopulation,
    ClimateObservation,
    DataQualityIssue,
    DataSource,
    ImportBatch,
    SivigilaReport,
)


class DuplicateBatchError(Exception):
    """El mismo archivo (por SHA-256) ya fue registrado para esa fuente; la recarga es idempotente."""


@dataclass(frozen=True)
class BatchInfo:
    source_code: str
    filename: str
    format_name: str
    file_sha256: str | None = None
    file_size_bytes: int | None = None
    source_version: str | None = None
    schema_fingerprint: str | None = None
    received_at: datetime | None = None
    completeness_status: str = "unknown"
    notes: str | None = None


def get_or_create_source(db: Session, *, code: str, name: str, institution: str | None = None) -> DataSource:
    source = db.scalar(select(DataSource).where(DataSource.code == code))
    if source is None:
        source = DataSource(code=code, name=name, institution=institution)
        db.add(source)
        db.flush()
    return source


def create_batch(db: Session, info: BatchInfo) -> ImportBatch:
    source = db.scalar(select(DataSource).where(DataSource.code == info.source_code))
    if source is None:
        raise ValueError(f"Fuente desconocida: {info.source_code!r}; créela con get_or_create_source.")
    if info.file_sha256:
        existing = db.scalar(select(ImportBatch).where(ImportBatch.source_id == source.id, ImportBatch.file_sha256 == info.file_sha256))
        if existing is not None:
            raise DuplicateBatchError(f"El archivo ya fue importado como lote {existing.id}.")
    batch = ImportBatch(
        source_id=source.id,
        source_filename=info.filename,
        file_sha256=info.file_sha256,
        file_size_bytes=info.file_size_bytes,
        source_version=info.source_version,
        schema_fingerprint=info.schema_fingerprint,
        format_name=info.format_name,
        received_at=info.received_at,
        transformation_version=TRANSFORMATION_VERSION,
        completeness_status=info.completeness_status,
        notes=info.notes,
    )
    db.add(batch)
    db.flush()
    return batch


def _record_issues(db: Session, batch: ImportBatch, entity: str, row: ValidatedRow) -> None:
    for issue in row.issues:
        db.add(
            DataQualityIssue(
                batch_id=batch.id,
                entity_name=entity,
                sheet_name=row.sheet_name or None,
                source_row_number=row.source_row_number,
                entity_key=issue.field,
                issue_code=issue.code,
                severity=issue.severity,
                evidence=issue.message,
            )
        )


def _finish_batch(batch: ImportBatch, rows: Sequence[ValidatedRow]) -> None:
    batch.rows_read = len(rows)
    statuses = {r.status for r in rows}
    if rows and statuses == {VALIDATION_REJECTED}:
        batch.validation_status = VALIDATION_REJECTED
    elif statuses <= {VALIDATION_VALID}:
        batch.validation_status = VALIDATION_VALID if rows else VALIDATION_PENDING
    else:
        batch.validation_status = VALIDATION_PENDING  # hay filas con reservas: el lote requiere revisión


def persist_sivigila(db: Session, batch: ImportBatch, rows: Sequence[ValidatedRow]) -> None:
    """Guarda TODAS las filas, incluidas las rechazadas y repetidas, con su estado."""
    for row in rows:
        db.add(SivigilaReport(batch_id=batch.id, sheet_name=row.sheet_name, source_row_number=row.source_row_number, validation_status=row.status, **row.record))
        _record_issues(db, batch, "sivigila_report", row)
    _finish_batch(batch, rows)
    db.flush()


def persist_climate(db: Session, batch: ImportBatch, rows: Sequence[ValidatedRow], station_ids: Mapping[str, int]) -> None:
    """`station_ids` mapea código IDEAM → weather_station.id. Sin estación cargada, una fila 'valid' pasa a 'pending'."""
    for row in rows:
        record = dict(row.record)
        station_id = station_ids.get(record.get("station_code_source") or "")
        if station_id is None and row.status == VALIDATION_VALID:
            row.add(Issue("station_not_loaded", SEVERITY_WARNING, "La estación aún no está en weather_station", "station"), status=VALIDATION_PENDING)
        db.add(ClimateObservation(batch_id=batch.id, sheet_name=row.sheet_name, source_row_number=row.source_row_number, station_id=station_id, validation_status=row.status, **record))
        _record_issues(db, batch, "climate_observation", row)
    _finish_batch(batch, rows)
    db.flush()


def persist_population(db: Session, batch: ImportBatch, rows: Sequence[ValidatedRow]) -> None:
    """Las filas rechazadas se registran solo como hallazgos: sus claves obligatorias pueden ser inválidas o nulas."""
    for row in rows:
        if row.status == VALIDATION_REJECTED:
            _record_issues(db, batch, "annual_population", row)
            continue
        db.add(AnnualPopulation(batch_id=batch.id, validation_status=row.status, **row.record))
        _record_issues(db, batch, "annual_population", row)
    _finish_batch(batch, rows)
    db.flush()


__all__ = ["BatchInfo", "DuplicateBatchError", "create_batch", "get_or_create_source", "persist_climate", "persist_population", "persist_sivigila"]
