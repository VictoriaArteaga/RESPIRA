from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.seed import seed_simulated_data
from app.models import IraCase, Municipality


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal.begin() as db:
        seed_simulated_data(db)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title="RESPIRA API",
    description="API para monitoreo académico de infecciones respiratorias agudas en Nariño.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(api_router)
