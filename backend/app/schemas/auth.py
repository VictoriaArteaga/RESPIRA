import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterRequest(BaseModel):
    # extra="forbid": un rol u otro campo enviado por el cliente se rechaza en lugar de ignorarse en silencio.
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("La contraseña debe incluir al menos una letra y un número.")
        return value

    @model_validator(mode="after")
    def _password_not_email(self) -> "RegisterRequest":
        if self.password.lower() == self.email:
            raise ValueError("La contraseña no puede ser igual al correo electrónico.")
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        return _normalize_email(value)


class RegisterAccepted(BaseModel):
    detail: str = "Solicitud recibida. Un administrador debe aprobar la cuenta antes de que puedas iniciar sesión."


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserRead(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin", "analyst"] | None = None
    is_active: bool | None = None
