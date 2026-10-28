import os

# Variables ficticias: la configuración exige DB_* y ninguna prueba se conecta a PostgreSQL.
os.environ.update(
    {
        "DB_HOST": "localhost",
        "DB_NAME": "test",
        "DB_USER": "test",
        "DB_PASSWORD": "test",
        "JWT_SECRET_KEY": "test-only-secret-key-not-for-production-0123456789",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "DB_CREATE_TABLES": "true",
        "DB_SEED_SIMULATED": "true",
    }
)

import pytest  # noqa: E402
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


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    from app.core import rate_limit

    rate_limit.reset_all()
    yield
    rate_limit.reset_all()
