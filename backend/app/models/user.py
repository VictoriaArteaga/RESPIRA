from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLES = (ROLE_ADMIN, ROLE_ANALYST)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'analyst')", name="ck_users_role_valid"),
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    # Inactiva por defecto: toda cuenta nueva requiere aprobación (o creación explícita por script/admin).
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    # Se incrementa al cerrar sesión o al cambiar rol/estado: invalida todos los tokens emitidos antes.
    token_version: Mapped[int] = mapped_column(Integer, server_default=text("0"), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
