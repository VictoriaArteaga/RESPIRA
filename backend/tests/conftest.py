import os

# Variables ficticias: la configuración exige DB_* y ninguna prueba se conecta a PostgreSQL.
os.environ.update(
    {
        "DB_HOST": "localhost",
        "DB_NAME": "test",
        "DB_USER": "test",
        "DB_PASSWORD": "test",
        "DB_CREATE_TABLES": "true",
        "DB_SEED_SIMULATED": "true",
    }
)

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core import database  # noqa: E402

# Las pruebas unitarias usan SQLite en memoria por velocidad y aislamiento; es una excepción
# confinada a este archivo y nunca se usa en ejecución real.
database.engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
database.SessionLocal.configure(bind=database.engine)
