"""Cargador y lector XLSX con datos SINTÉTICOS en SQLite. No se leen datasets oficiales ni se toca Supabase."""

import pytest
from openpyxl import Workbook
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.importers import ideam, sivigila
from app.importers.common import file_sha256
from app.importers.loader import BatchInfo, DuplicateBatchError, create_batch, get_or_create_source, persist_climate, persist_sivigila
from app.models import ClimateObservation, DataQualityIssue, ImportBatch, SivigilaReport, WeatherStation

HEADERS = ["COD_EVE", "COD_MUN", "AÑO", "SEMANA", "COD_PRE", "COD_SUB", "NUM_CON", "IRACEXT_1", "IRACEXT_2", "IRACEXT_3", "FEC_NOT"]


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
def workbook(tmp_path):
    path = tmp_path / "sintetico_995.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Hoja1"
    ws.append(HEADERS)
    ws.append([995, 52240, 2016, 43, "P1", "1", 263, 8, 0, 0, "2016-10-25"])
    ws.append([995, 52240, 2016, 43, "P1", "1", 264, 1, 0, 0, "2016-10-26"])  # mismo prestador-semana, otro NUM_CON
    ws.append([995, 52240, 2016, 99, "P2", "1", 1, 1, 1, 1, None])  # semana inválida
    ws.append([995, 52240, 2016, 44, "P3", "1", 1, None, None, None, None])  # conteos vacíos
    ws.append([None] * 11)  # fila vacía: se omite
    wb.save(path)
    return path


def test_xlsx_reader_reports_excel_row_numbers_and_skips_blank_rows(workbook):
    rows = list(sivigila.read_xlsx(workbook, sheet_name="Hoja1"))
    assert [n for n, _ in rows] == [2, 3, 4, 5]
    assert rows[0][1]["report_consecutive"] == 263


def test_xlsx_reader_rejects_unknown_sheet(workbook):
    with pytest.raises(Exception, match="no existe"):
        list(sivigila.read_xlsx(workbook, sheet_name="Nope"))


def test_end_to_end_sivigila_load_keeps_every_row_and_traces_issues(db, workbook):
    rows = [sivigila.validate_row(raw, sheet_name="Hoja1", source_row_number=n) for n, raw in sivigila.read_xlsx(workbook, sheet_name="Hoja1")]
    assert sivigila.flag_repeats(rows) == 1

    get_or_create_source(db, code="sivigila_995", name="SIVIGILA evento 995", institution="INS")
    batch = create_batch(db, BatchInfo(source_code="sivigila_995", filename=workbook.name, format_name="xlsx", file_sha256=file_sha256(workbook)))
    persist_sivigila(db, batch, rows)
    db.commit()

    stored = db.scalars(select(SivigilaReport).order_by(SivigilaReport.source_row_number)).all()
    assert [r.source_row_number for r in stored] == [2, 3, 4, 5]
    assert [r.validation_status for r in stored] == ["valid", "valid", "rejected", "missing"]
    assert [r.report_group_status for r in stored[:2]] == ["unresolved_repeat"] * 2
    assert [r.ira_ext_under1 for r in stored] == [8, 1, 1, None]  # el vacío sigue siendo NULL
    assert {r.report_consecutive for r in stored[:2]} == {"263", "264"}
    codes = set(db.scalars(select(DataQualityIssue.issue_code)))
    assert {"repeated_provider_week", "week_out_of_range", "all_counts_missing"} <= codes
    assert db.get(ImportBatch, batch.id).validation_status == "pending" and batch.rows_read == 4
    assert batch.transformation_version


def test_same_file_cannot_be_registered_twice(db, workbook):
    get_or_create_source(db, code="sivigila_995", name="SIVIGILA")
    info = BatchInfo(source_code="sivigila_995", filename=workbook.name, format_name="xlsx", file_sha256=file_sha256(workbook))
    create_batch(db, info)
    with pytest.raises(DuplicateBatchError):
        create_batch(db, info)


def test_unknown_source_is_an_error(db):
    with pytest.raises(ValueError):
        create_batch(db, BatchInfo(source_code="nope", filename="f", format_name="x"))


def test_climate_rows_without_loaded_station_are_downgraded_to_pending(db, tmp_path):
    path = tmp_path / "TSSM_MN_D@52045020.data"
    path.write_text("Fecha|Valor\n2016-01-03 07:00:00|15.0\n2016-01-04 07:00:00|\n", encoding="utf-8")
    variable, station = ideam.parse_filename(path)
    rows = [ideam.validate_observation(raw, station_code=station, variable_code=variable, source_row_number=n) for n, raw in ideam.read_data_file(path)]

    get_or_create_source(db, code="ideam", name="IDEAM")
    batch = create_batch(db, BatchInfo(source_code="ideam", filename=path.name, format_name="ideam-data"))
    persist_climate(db, batch, rows, station_ids={})
    assert [r.validation_status for r in db.scalars(select(ClimateObservation).order_by(ClimateObservation.source_row_number))] == ["pending", "missing"]

    station_row = WeatherStation(ideam_station_code=station)
    db.add(station_row)
    db.flush()
    rows2 = [ideam.validate_observation(raw, station_code=station, variable_code=variable, source_row_number=n) for n, raw in ideam.read_data_file(path)]
    batch2 = create_batch(db, BatchInfo(source_code="ideam", filename="again.data", format_name="ideam-data"))
    persist_climate(db, batch2, rows2, station_ids={station: station_row.id})
    statuses = db.scalars(select(ClimateObservation.validation_status).where(ClimateObservation.batch_id == batch2.id).order_by(ClimateObservation.source_row_number)).all()
    assert statuses == ["valid", "missing"]


def test_rollback_leaves_no_trace(db, workbook):
    get_or_create_source(db, code="sivigila_995", name="SIVIGILA")
    db.commit()
    batch = create_batch(db, BatchInfo(source_code="sivigila_995", filename="f", format_name="xlsx"))
    persist_sivigila(db, batch, [sivigila.validate_row(raw, sheet_name="Hoja1", source_row_number=n) for n, raw in sivigila.read_xlsx(workbook, sheet_name="Hoja1")])
    db.rollback()
    assert db.scalar(select(func.count()).select_from(SivigilaReport)) == 0
    assert db.scalar(select(func.count()).select_from(ImportBatch)) == 0
