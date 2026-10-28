from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

TOKEN_ISSUER = "respira-api"
_REQUIRED_CLAIMS = ["exp", "iat", "sub", "iss", "tv"]

# PasswordHasher usa Argon2id por defecto.
_hasher = PasswordHasher()
# Hash de relleno para igualar el tiempo de respuesta cuando el correo no existe.
_DUMMY_HASH = _hasher.hash("respira-dummy-password-for-timing")


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def burn_password_check(password: str) -> None:
    verify_password(_DUMMY_HASH, password)


def create_access_token(user_id: int, token_version: int) -> tuple[str, int]:
    """Devuelve el token firmado y su duración en segundos."""
    now = datetime.now(timezone.utc)
    lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "tv": token_version,
        "iss": TOKEN_ISSUER,
        "iat": now,
        "exp": now + lifetime,
    }
    token = jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> tuple[int, int]:
    """Valida firma, expiración, emisor y campos obligatorios; devuelve (user_id, token_version)."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=TOKEN_ISSUER,
            options={"require": _REQUIRED_CLAIMS},
        )
        user_id = int(payload["sub"])
        token_version = payload["tv"]
    except (jwt.PyJWTError, ValueError, TypeError) as error:
        raise InvalidTokenError from error
    if isinstance(token_version, bool) or not isinstance(token_version, int):
        raise InvalidTokenError
    return user_id, token_version
