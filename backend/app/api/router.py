from fastapi import APIRouter, Depends

from app.api.dependencies import require_analyst
from app.api.routes import admin_users, auth, cases, dashboard, health, municipalities, risk

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin_users.router, prefix="/admin/users", tags=["admin"])

# Las funciones de análisis epidemiológico exigen una sesión con rol analyst o admin.
protected = [Depends(require_analyst)]
api_router.include_router(municipalities.router, prefix="/municipalities", tags=["municipalities"], dependencies=protected)
api_router.include_router(risk.router, tags=["risk-analysis"], dependencies=protected)
api_router.include_router(cases.router, prefix="/cases", tags=["cases"], dependencies=protected)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=protected)
