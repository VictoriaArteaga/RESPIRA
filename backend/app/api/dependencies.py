from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import InvalidTokenError, decode_access_token
from app.models.user import ROLE_ADMIN, ROLE_ANALYST, User
from app.repositories.user_repository import UserRepository

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación no válidas.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized()
    try:
        user_id, token_version = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise _unauthorized() from None
    user = UserRepository(db).get_by_id(user_id)
    # token_version distinto => sesión cerrada o permisos modificados; cuenta inactiva => acceso retirado.
    if user is None or not user.is_active or user.token_version != token_version:
        raise _unauthorized()
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes.")
        return user

    return dependency


require_analyst = require_roles(ROLE_ANALYST, ROLE_ADMIN)
require_admin = require_roles(ROLE_ADMIN)
