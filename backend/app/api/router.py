from fastapi import APIRouter

from app.api.routes import cases, dashboard, health, municipalities

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(municipalities.router, prefix="/municipalities", tags=["municipalities"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
