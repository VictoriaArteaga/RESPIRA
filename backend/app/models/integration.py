"""Modelo de integración de datos oficiales (Fase 2.2).

Capa de datos FUENTE normalizados con trazabilidad (fuente → lote → fila de origen). No contiene
indicadores derivados ni agregados: dependen de decisiones pendientes (D-01, D-02, D-15) y se modelarán después.
`ira_cases` sigue siendo el modelo inicial de la aplicación; los datos reales entran por estas tablas.

Reglas de diseño:
- Un valor ausente es NULL con `validation_status = 'missing'`; nunca se convierte en cero.
- Los reportes SIVIGILA no tienen UNIQUE por prestador/semana: las repeticiones se conservan y se marcan.
- Las restricciones con expresiones regulares solo se emiten en PostgreSQL (`ddl_if`); SQLite, usado en las
  pruebas unitarias, conserva las demás. Los validadores en `app.importers` cubren ambos casos.
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# BIGINT en PostgreSQL (SIVIGILA 2021 supera el millón de filas); INTEGER en SQLite para que autoincremente.
BigId = BigInteger().with_variant(Integer, "sqlite")

VALIDATION_VALID = "valid"
VALIDATION_PENDING = "pending"
VALIDATION_REJECTED = "rejected"
VALIDATION_MISSING = "missing"
VALIDATION_DERIVED = "derived"
VALIDATION_STATUSES = (
    VALIDATION_VALID,
    VALIDATION_PENDING,
    VALIDATION_REJECTED,
    VALIDATION_MISSING,
    VALIDATION_DERIVED,
)
COMPLETENESS_STATUSES = ("unknown", "claimed_complete", "verified_complete", "known_limited", "rejected")
REPORT_GROUP_STATUSES = (
    "unreviewed",
    "single_report",
    "unresolved_repeat",
    "official_correction_confirmed",
    "excluded_with_reason",
)
SEVERITIES = ("info", "warning", "blocking")
ISSUE_STATUSES = ("open", "resolved", "accepted_with_caveat")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _regex(column: str, pattern: str, name: str) -> CheckConstraint:
    return CheckConstraint(f"{column} ~ '{pattern}'", name=name).ddl_if(dialect="postgresql")


class DataSource(Base):
    __tablename__ = "data_source"

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class ImportBatch(Base):
    """Una recepción concreta de un archivo fuente. El archivo original nunca se modifica ni se almacena aquí."""

    __tablename__ = "import_batch"
    __table_args__ = (
        CheckConstraint("file_size_bytes IS NULL OR file_size_bytes >= 0", name="ck_import_batch_size_non_negative"),
        CheckConstraint(_in("completeness_status", COMPLETENESS_STATUSES), name="ck_import_batch_completeness_valid"),
        CheckConstraint(_in("validation_status", VALIDATION_STATUSES), name="ck_import_batch_validation_valid"),
        CheckConstraint("file_sha256 IS NULL OR length(file_sha256) = 64", name="ck_import_batch_sha256_length"),
        _regex("file_sha256", "^[0-9a-f]{64}$", "ck_import_batch_sha256_hex"),
        # Idempotencia: el mismo archivo (por hash) de una fuente no crea un segundo lote.
        Index(
            "uq_import_batch_source_sha256",
            "source_id",
            "file_sha256",
            unique=True,
            postgresql_where=text("file_sha256 IS NOT NULL"),
            sqlite_where=text("file_sha256 IS NOT NULL"),
        ),
        Index("ix_import_batch_source_id", "source_id"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_source.id"))
    source_filename: Mapped[str] = mapped_column(String(300))
    file_sha256: Mapped[str | None] = mapped_column(String(64))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    source_version: Mapped[str | None] = mapped_column(String(100))
    schema_fingerprint: Mapped[str | None] = mapped_column(String(64))
    format_name: Mapped[str] = mapped_column(String(60))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Versión de las reglas de lectura/validación aplicadas: permite reproducir y auditar la transformación.
    transformation_version: Mapped[str] = mapped_column(String(40))
    rows_read: Mapped[int | None] = mapped_column(BigInteger)
    completeness_status: Mapped[str] = mapped_column(String(20), server_default=text("'unknown'"))
    validation_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))
    notes: Mapped[str | None] = mapped_column(Text)


class WeatherStation(Base):
    __tablename__ = "weather_station"
    __table_args__ = (
        CheckConstraint(_in("validation_status", VALIDATION_STATUSES), name="ck_weather_station_validation_valid"),
        CheckConstraint("latitude IS NULL OR latitude BETWEEN -90 AND 90", name="ck_weather_station_latitude_range"),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name="ck_weather_station_longitude_range"
        ),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    ideam_station_code: Mapped[str] = mapped_column(String(20), unique=True)
    catalog_name: Mapped[str | None] = mapped_column(String(200))
    municipality_code: Mapped[str | None] = mapped_column(String(5))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    altitude_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    station_status: Mapped[str | None] = mapped_column(String(60))
    catalog_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batch.id"))
    validation_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))


class SivigilaReport(Base):
    """Fila fuente del evento 995. Una fila = un reporte colectivo, no un paciente ni un caso único."""

    __tablename__ = "sivigila_report"
    __table_args__ = (
        UniqueConstraint("batch_id", "sheet_name", "source_row_number", name="uq_sivigila_report_source_row"),
        CheckConstraint("source_row_number > 0", name="ck_sivigila_report_row_positive"),
        CheckConstraint("epi_year IS NULL OR epi_year BETWEEN 2000 AND 2100", name="ck_sivigila_report_year_range"),
        CheckConstraint("epi_week IS NULL OR epi_week BETWEEN 1 AND 53", name="ck_sivigila_report_week_range"),
        CheckConstraint("municipality_code IS NULL OR length(municipality_code) = 5", name="ck_sivigila_report_muni_len"),
        _regex("municipality_code", "^[0-9]{5}$", "ck_sivigila_report_muni_format"),
        CheckConstraint("ira_ext_under1 IS NULL OR ira_ext_under1 >= 0", name="ck_sivigila_report_under1_non_negative"),
        CheckConstraint("ira_ext_age1 IS NULL OR ira_ext_age1 >= 0", name="ck_sivigila_report_age1_non_negative"),
        CheckConstraint("ira_ext_age2_4 IS NULL OR ira_ext_age2_4 >= 0", name="ck_sivigila_report_age2_4_non_negative"),
        CheckConstraint(_in("validation_status", VALIDATION_STATUSES), name="ck_sivigila_report_validation_valid"),
        CheckConstraint(_in("report_group_status", REPORT_GROUP_STATUSES), name="ck_sivigila_report_group_valid"),
        # Una fila 'valid' debe poder ubicarse en el tiempo y el territorio; las demás se conservan con lo que tengan.
        CheckConstraint(
            "validation_status <> 'valid' OR (epi_year IS NOT NULL AND epi_week IS NOT NULL "
            "AND municipality_code IS NOT NULL)",
            name="ck_sivigila_report_valid_requires_period",
        ),
        Index("ix_sivigila_report_period", "municipality_code", "epi_year", "epi_week"),
        # No es UNIQUE a propósito (D-01): agrupa las filas repetidas de un mismo prestador/semana para revisarlas.
        Index("ix_sivigila_report_provider_group", "provider_code", "provider_subsite_code", "epi_year", "epi_week"),
        Index("ix_sivigila_report_batch_id", "batch_id"),
        Index("ix_sivigila_report_municipality_id", "municipality_id"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"))
    sheet_name: Mapped[str] = mapped_column(String(100))
    source_row_number: Mapped[int] = mapped_column(BigInteger)
    # Código DIVIPOLA tal como viene de la fuente (texto de 5 dígitos); municipality_id se resuelve cuando exista el catálogo.
    municipality_code: Mapped[str | None] = mapped_column(String(5))
    municipality_id: Mapped[int | None] = mapped_column(ForeignKey("municipalities.id"))
    epi_year: Mapped[int | None] = mapped_column(SmallInteger)
    epi_week: Mapped[int | None] = mapped_column(SmallInteger)
    notification_date: Mapped[date | None] = mapped_column(Date)
    event_code: Mapped[str | None] = mapped_column(String(10))
    provider_code: Mapped[str | None] = mapped_column(String(30))
    provider_subsite_code: Mapped[str | None] = mapped_column(String(30))
    report_consecutive: Mapped[str | None] = mapped_column(String(30))  # NUM_CON: no se usa para deduplicar
    ira_ext_under1: Mapped[int | None] = mapped_column(Integer)
    ira_ext_age1: Mapped[int | None] = mapped_column(Integer)
    ira_ext_age2_4: Mapped[int | None] = mapped_column(Integer)
    validation_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))
    report_group_status: Mapped[str] = mapped_column(String(40), server_default=text("'unreviewed'"))


class ClimateObservation(Base):
    """Observación diaria estación-variable-fecha tal como llega de IDEAM. No es un agregado semanal."""

    __tablename__ = "climate_observation"
    __table_args__ = (
        UniqueConstraint("batch_id", "sheet_name", "source_row_number", name="uq_climate_observation_source_row"),
        CheckConstraint("source_row_number > 0", name="ck_climate_observation_row_positive"),
        CheckConstraint(_in("validation_status", VALIDATION_STATUSES), name="ck_climate_observation_validation_valid"),
        # Faltante y valor son excluyentes: un dato ausente jamás se guarda como 0.
        CheckConstraint(
            "validation_status <> 'missing' OR value_numeric IS NULL", name="ck_climate_observation_missing_is_null"
        ),
        CheckConstraint(
            "validation_status <> 'valid' OR (value_numeric IS NOT NULL AND observed_date IS NOT NULL "
            "AND station_id IS NOT NULL)",
            name="ck_climate_observation_valid_requires_value",
        ),
        Index("ix_climate_observation_station_date", "station_id", "observed_date", "variable_code"),
        Index("ix_climate_observation_batch_id", "batch_id"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"))
    sheet_name: Mapped[str] = mapped_column(String(100), server_default=text("''"))
    source_row_number: Mapped[int] = mapped_column(BigInteger)
    station_id: Mapped[int | None] = mapped_column(ForeignKey("weather_station.id"))
    station_code_source: Mapped[str | None] = mapped_column(String(20))
    observed_date: Mapped[date | None] = mapped_column(Date)
    variable_code: Mapped[str] = mapped_column(String(40))
    value_numeric: Mapped[float | None] = mapped_column(Numeric(16, 6))
    value_text_original: Mapped[str | None] = mapped_column(String(60))
    unit_original: Mapped[str | None] = mapped_column(String(30))
    validation_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))


class AnnualPopulation(Base):
    """Proyección anual DANE. Se guarda una vez por año: no se replica por semana."""

    __tablename__ = "annual_population"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "municipality_code",
            "reference_year",
            "population_area",
            "age_min",
            "age_max",
            "sex_code",
            name="uq_annual_population_key",
        ),
        CheckConstraint("population_count IS NULL OR population_count >= 0", name="ck_annual_population_non_negative"),
        CheckConstraint("reference_year BETWEEN 1950 AND 2100", name="ck_annual_population_year_range"),
        CheckConstraint("age_min >= 0 AND age_max >= age_min", name="ck_annual_population_age_range"),
        CheckConstraint("length(municipality_code) = 5", name="ck_annual_population_muni_len"),
        _regex("municipality_code", "^[0-9]{5}$", "ck_annual_population_muni_format"),
        CheckConstraint(_in("validation_status", VALIDATION_STATUSES), name="ck_annual_population_validation_valid"),
        CheckConstraint(
            "validation_status <> 'missing' OR population_count IS NULL", name="ck_annual_population_missing_is_null"
        ),
        Index("ix_annual_population_batch_id", "batch_id"),
        Index("ix_annual_population_municipality", "municipality_code", "reference_year"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"))
    municipality_code: Mapped[str] = mapped_column(String(5))
    municipality_id: Mapped[int | None] = mapped_column(ForeignKey("municipalities.id"))
    reference_year: Mapped[int] = mapped_column(SmallInteger)
    population_area: Mapped[str] = mapped_column(String(30))
    age_min: Mapped[int] = mapped_column(SmallInteger)
    age_max: Mapped[int] = mapped_column(SmallInteger)
    sex_code: Mapped[str] = mapped_column(String(20))
    population_count: Mapped[int | None] = mapped_column(BigInteger)
    workbook_version: Mapped[str | None] = mapped_column(String(100))
    validation_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))


class DataQualityIssue(Base):
    """Hallazgo de calidad. Los rechazos y las advertencias se registran aquí en lugar de descartarse en silencio."""

    __tablename__ = "data_quality_issue"
    __table_args__ = (
        CheckConstraint(_in("severity", SEVERITIES), name="ck_data_quality_issue_severity_valid"),
        CheckConstraint(_in("issue_status", ISSUE_STATUSES), name="ck_data_quality_issue_status_valid"),
        Index("ix_data_quality_issue_batch_id", "batch_id"),
        Index("ix_data_quality_issue_code", "issue_code"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batch.id"))
    entity_name: Mapped[str] = mapped_column(String(60))
    sheet_name: Mapped[str | None] = mapped_column(String(100))
    source_row_number: Mapped[int | None] = mapped_column(BigInteger)
    entity_key: Mapped[str | None] = mapped_column(String(200))
    issue_code: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(10))
    issue_status: Mapped[str] = mapped_column(String(25), server_default=text("'open'"))
    evidence: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
