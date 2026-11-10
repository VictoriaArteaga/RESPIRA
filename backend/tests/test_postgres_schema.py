"""Pruebas contra un PostgreSQL REAL y DESECHABLE: migraciones 0001→0003, deriva modelos↔migración y restricciones.

Se omiten salvo que `RESPIRA_TEST_PG_URL` apunte a una base vacía creada para pruebas, p. ej.
    postgresql+psycopg://usuario:clave@127.0.0.1:5432/respira_test
Salvaguardas: el nombre de la base debe contener "test" o "scratch", el host no puede ser un proveedor remoto
conocido y la base debe estar vacía. NUNCA apuntar a Supabase: la prueba aplica y revierte migraciones.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

PG_URL = os.environ.get("RESPIRA_TEST_PG_URL")
pytestmark = pytest.mark.skipif(not PG_URL, reason="RESPIRA_TEST_PG_URL no definida (requiere PostgreSQL desechable)")
BACKEND = Path(__file__).resolve().parents[1]
NEW_TABLES = {"data_source", "import_batch", "weather_station", "sivigila_report", "climate_observation", "annual_population", "data_quality_issue"}


def _alembic(url, *args):
    env = {
        **os.environ,
        "DB_HOST": url.host, "DB_PORT": str(url.port or 5432), "DB_NAME": url.database, "DB_USER": url.username or "",
        "DB_PASSWORD": url.password or "x", "DB_SSLMODE": "prefer",
        "JWT_SECRET_KEY": "test-only-secret-key-not-for-production-0123456789",
    }
    return subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, capture_output=True, text=True, check=True)


@pytest.fixture(scope="module")
def pg():
    url = make_url(PG_URL)
    assert url.database and any(t in url.database for t in ("test", "scratch")), "la base de pruebas debe llamarse *test* o *scratch*"
    assert "supabase" not in (url.host or "") and "pooler" not in (url.host or ""), "NUNCA usar Supabase"
    engine = create_engine(url)
    with engine.connect() as conn:
        assert not set(inspect(conn).get_table_names()) - {"alembic_version"}, "la base de pruebas debe estar vacía"
    _alembic(url, "upgrade", "head")
    yield engine
    _alembic(url, "downgrade", "base")
    engine.dispose()


def test_migrations_create_new_tables_and_keep_phase1_tables(pg):
    tables = set(inspect(pg).get_table_names())
    assert NEW_TABLES | {"municipalities", "ira_cases", "users"} <= tables


def test_models_and_migrations_have_no_drift(pg):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    from app.core.database import Base
    import app.models  # noqa: F401

    with pg.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []


def test_0003_downgrade_and_upgrade_roundtrip_preserves_phase1(pg):
    url = pg.url
    _alembic(url, "downgrade", "0002")
    tables = set(inspect(pg).get_table_names())
    assert not NEW_TABLES & tables and {"municipalities", "ira_cases", "users"} <= tables
    _alembic(url, "upgrade", "head")
    assert NEW_TABLES <= set(inspect(pg).get_table_names())


@pytest.fixture()
def conn(pg):
    """Conexión con transacción externa que siempre se revierte: no queda ningún dato."""
    with pg.connect() as connection:
        outer = connection.begin()
        connection.execute(text("INSERT INTO data_source(code, name) VALUES ('t', 't')"))
        connection.execute(text("INSERT INTO import_batch(source_id, source_filename, format_name, transformation_version) SELECT id, 'f', 'xlsx', 't' FROM data_source"))
        yield connection
        outer.rollback()


def _fails(conn, sql, **params):
    nested = conn.begin_nested()
    with pytest.raises(IntegrityError):
        conn.execute(text(sql), params)
    nested.rollback()


BASE = "INSERT INTO sivigila_report(batch_id, sheet_name, source_row_number, municipality_code, epi_year, epi_week, validation_status) SELECT id, 's', {row}, '{code}', {year}, {week}, 'valid' FROM import_batch"


@pytest.mark.parametrize("code,year,week", [("5224", 2016, 10), ("ABCDE", 2016, 10), ("5224A", 2016, 10), ("52240", 2016, 54), ("52240", 1999, 10)])
def test_pg_sivigila_constraints(conn, code, year, week):
    _fails(conn, BASE.format(row=1, code=code, year=year, week=week))


def test_pg_regex_constraints_reject_non_digit_codes_and_bad_hashes(conn):
    _fails(conn, "INSERT INTO annual_population(batch_id, municipality_code, reference_year, population_area, age_min, age_max, sex_code) SELECT id, '52A01', 2020, 'T', 0, 4, 'T' FROM import_batch")
    _fails(conn, "INSERT INTO import_batch(source_id, source_filename, format_name, transformation_version, file_sha256) SELECT id, 'f', 'x', 't', repeat('Z', 64) FROM data_source")


def test_pg_accepts_valid_row_and_repeated_provider_week(conn):
    conn.execute(text(BASE.format(row=1, code="52240", year=2016, week=43)))
    conn.execute(text(BASE.format(row=2, code="52240", year=2016, week=43)))  # misma clave de negocio, otra fila fuente
    assert conn.execute(text("SELECT count(*) FROM sivigila_report")).scalar() == 2


def test_pg_source_row_unique_and_fk(conn):
    conn.execute(text(BASE.format(row=1, code="52240", year=2016, week=43)))
    _fails(conn, BASE.format(row=1, code="52240", year=2016, week=43))
    _fails(conn, "INSERT INTO sivigila_report(batch_id, sheet_name, source_row_number) VALUES (999999, 's', 9)")
    _fails(conn, "INSERT INTO sivigila_report(batch_id, sheet_name, source_row_number, municipality_id) SELECT id, 's', 8, 999999 FROM import_batch")


def test_pg_missing_climate_value_cannot_be_zero(conn):
    _fails(conn, "INSERT INTO climate_observation(batch_id, source_row_number, variable_code, value_numeric, validation_status) SELECT id, 1, 'V', 0, 'missing' FROM import_batch")
