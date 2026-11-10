"""Restricciones del modelo de integración, comprobadas en SQLite con una base aislada por prueba.

Aquí solo se prueban las restricciones portables. Las específicas de PostgreSQL (formato por expresión regular,
migración 0003, deriva modelos↔migración) las cubre `test_postgres_schema.py`, que requiere un PostgreSQL desechable.
"""

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import (
    AnnualPopulation,
    ClimateObservation,
    DataQualityIssue,
    DataSource,
    ImportBatch,
    IraCase,
    Municipality,
    SivigilaReport,
    WeatherStation,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def batch(db):
    source = DataSource(code="sivigila_995", name="SIVIGILA 995")
    db.add(source)
    db.flush()
    batch = ImportBatch(source_id=source.id, source_filename="x.xlsx", format_name="xlsx", transformation_version="t")
    db.add(batch)
    db.commit()  # las pruebas hacen rollback tras cada violación: la base ya debe estar confirmada
    return batch


def _report(batch, row=1, **overrides):
    values = dict(batch_id=batch.id, sheet_name="995", source_row_number=row, municipality_code="52240", epi_year=2016, epi_week=43, validation_status="valid")
    values.update(overrides)
    return SivigilaReport(**values)


def _expect_integrity_error(db, obj):
    db.add(obj)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_phase1_tables_are_untouched():
    assert {"municipalities", "ira_cases", "users"} <= set(Base.metadata.tables)
    assert IraCase.__table__.c.temperature.nullable is False  # modelo inicial de la app: sin cambios


@pytest.mark.parametrize("week", [0, 54, -1])
def test_sivigila_rejects_invalid_week(db, batch, week):
    _expect_integrity_error(db, _report(batch, epi_week=week))


@pytest.mark.parametrize("year", [1999, 2101])
def test_sivigila_rejects_invalid_year(db, batch, year):
    _expect_integrity_error(db, _report(batch, epi_year=year))


@pytest.mark.parametrize("field", ["ira_ext_under1", "ira_ext_age1", "ira_ext_age2_4"])
def test_sivigila_rejects_negative_counts(db, batch, field):
    _expect_integrity_error(db, _report(batch, **{field: -1}))


def test_sivigila_valid_row_requires_period_and_municipality(db, batch):
    _expect_integrity_error(db, _report(batch, epi_week=None))
    _expect_integrity_error(db, _report(batch, municipality_code=None))


def test_sivigila_unvalidated_row_may_keep_partial_data(db, batch):
    db.add(_report(batch, epi_week=None, validation_status="rejected"))
    db.flush()


def test_sivigila_keeps_repeated_provider_week_reports(db, batch):
    """D-01: dos reportes de la misma UPGD/semana con distinto NUM_CON coexisten; no hay unicidad por prestador."""
    common = dict(provider_code="520010001", provider_subsite_code="01", ira_ext_under1=5)
    db.add_all([_report(batch, 10, report_consecutive="263", **common), _report(batch, 11, report_consecutive="264", **common)])
    db.flush()
    assert len(db.scalars(select(SivigilaReport)).all()) == 2


def test_sivigila_source_row_is_unique_per_batch(db, batch):
    db.add(_report(batch, 5))
    db.flush()
    _expect_integrity_error(db, _report(batch, 5))


def test_sivigila_requires_existing_batch_and_municipality(db, batch):
    _expect_integrity_error(db, _report(batch, batch_id=9999))
    _expect_integrity_error(db, _report(batch, municipality_id=9999))


def test_sivigila_can_reference_existing_municipality(db, batch):
    municipality = Municipality(name="Chachagüí", latitude=1.36, longitude=-77.28)
    db.add(municipality)
    db.flush()
    db.add(_report(batch, municipality_id=municipality.id))
    db.flush()


def test_climate_missing_value_is_null_not_zero(db, batch):
    station = WeatherStation(ideam_station_code="52045020")
    db.add(station)
    db.commit()
    common = dict(batch_id=batch.id, station_id=station.id, variable_code="TSSM_MN_D")
    _expect_integrity_error(db, ClimateObservation(source_row_number=1, validation_status="missing", value_numeric=0, **common))
    db.add(ClimateObservation(source_row_number=2, validation_status="missing", value_numeric=None, **common))
    db.flush()


def test_climate_valid_row_requires_value_date_and_station(db, batch):
    _expect_integrity_error(db, ClimateObservation(batch_id=batch.id, source_row_number=1, variable_code="V", validation_status="valid", value_numeric=1.0))


def test_climate_zero_is_a_legitimate_value(db, batch):
    station = WeatherStation(ideam_station_code="1")
    db.add(station)
    db.flush()
    from datetime import date

    db.add(ClimateObservation(batch_id=batch.id, source_row_number=1, station_id=station.id, observed_date=date(2020, 1, 1), variable_code="PTPM_CON_INTER", value_numeric=0, validation_status="valid"))
    db.flush()


def test_weather_station_code_is_unique_and_coordinates_bounded(db):
    db.add(WeatherStation(ideam_station_code="1"))
    db.flush()
    _expect_integrity_error(db, WeatherStation(ideam_station_code="1"))
    _expect_integrity_error(db, WeatherStation(ideam_station_code="2", latitude=91))


def test_population_rejects_negative_and_bad_year_and_ages(db, batch):
    base = dict(batch_id=batch.id, municipality_code="52001", reference_year=2020, population_area="Total", age_min=0, age_max=4, sex_code="Total", population_count=10)
    _expect_integrity_error(db, AnnualPopulation(**{**base, "population_count": -1}))
    _expect_integrity_error(db, AnnualPopulation(**{**base, "reference_year": 1900}))
    _expect_integrity_error(db, AnnualPopulation(**{**base, "age_min": 5, "age_max": 4}))
    _expect_integrity_error(db, AnnualPopulation(**{**base, "validation_status": "missing"}))


def test_population_key_is_unique_per_batch(db, batch):
    base = dict(batch_id=batch.id, municipality_code="52001", reference_year=2020, population_area="Total", age_min=0, age_max=4, sex_code="Total", population_count=10)
    db.add(AnnualPopulation(**base))
    db.flush()
    _expect_integrity_error(db, AnnualPopulation(**base))


def test_import_batch_is_idempotent_by_sha256(db, batch):
    digest = "a" * 64
    batch.file_sha256 = digest
    db.flush()
    _expect_integrity_error(db, ImportBatch(source_id=batch.source_id, source_filename="y", format_name="xlsx", transformation_version="t", file_sha256=digest))
    # Sin hash no hay unicidad: dos recepciones sin huella se permiten (y quedan como 'unknown').
    db.add_all([ImportBatch(source_id=batch.source_id, source_filename=n, format_name="xlsx", transformation_version="t") for n in ("a", "b")])
    db.flush()


def test_import_batch_rejects_bad_sha_length_and_status(db, batch):
    for bad in ({"file_sha256": "abc"}, {"validation_status": "ok"}, {"completeness_status": "complete"}, {"file_size_bytes": -1}):
        _expect_integrity_error(db, ImportBatch(source_id=batch.source_id, source_filename="z", format_name="xlsx", transformation_version="t", **bad))


def test_quality_issue_vocabularies(db, batch):
    db.add(DataQualityIssue(batch_id=batch.id, entity_name="sivigila_report", issue_code="x", severity="warning"))
    db.flush()
    _expect_integrity_error(db, DataQualityIssue(entity_name="e", issue_code="x", severity="fatal"))


def test_municipality_divipola_is_optional_unique_and_coordinates_are_optional_but_paired(db):
    db.add_all([Municipality(name="Sintético"), Municipality(name="Otro sintético", latitude=1.0, longitude=-77.0)])  # DIVIPOLA nulo repetible
    db.add(Municipality(name="Pasto", divipola_code="52001"))  # sin coordenadas verificadas
    db.commit()
    _expect_integrity_error(db, Municipality(name="Duplicado", divipola_code="52001"))
    _expect_integrity_error(db, Municipality(name="Corto", divipola_code="5200"))
    _expect_integrity_error(db, Municipality(name="Media coordenada", latitude=1.0))


def test_app_only_exposes_municipalities_with_coordinates(db):
    from app.repositories.municipality_repository import MunicipalityRepository

    located = Municipality(name="Con coordenadas", latitude=1.2, longitude=-77.3)
    unlocated = Municipality(name="Sin coordenadas", divipola_code="52001")
    db.add_all([located, unlocated])
    db.commit()
    repo = MunicipalityRepository(db)
    assert [m.name for m in repo.list_all()] == ["Con coordenadas"]
    assert repo.count_all() == 1 and repo.get_by_id(unlocated.id) is None and repo.get_by_id(located.id) is not None
