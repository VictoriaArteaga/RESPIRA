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

    @property
    def status(self) -> str:
        """Estado derivado para la administración: pending, active o disabled.

        No hay un campo explícito de aprobación: una cuenta inactiva con token_version == 0 nunca fue activada
        (AuthService.update_user solo incrementa el contador si la cuenta estaba o queda activa), así que sigue
        pendiente; si no, fue desactivada.

        Limitaciones: (1) una cuenta activa devuelta a inactiva por SQL directo o restaurada con token_version = 0
        se vería como pendiente; (2) no existe el estado "rechazada": desactivar una cuenta pendiente la deja
        pendiente. Resolverlo exige un campo explícito (p. ej. approved_at) con migración.
        """
        if self.is_active:
            return "active"
        return "pending" if self.token_version == 0 else "disabled"
