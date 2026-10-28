from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import login_ip_limiter, login_pair_limiter, register_limiter
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterAccepted, RegisterRequest, TokenResponse, UserRead
from app.services.auth_service import AccountDisabled, AuthService, InvalidCredentials

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def _client_ip(request: Request) -> str:
    # No se confía en X-Forwarded-For: sin un proxy de confianza cualquier cliente podría falsearlo.
    return request.client.host if request.client else "unknown"


def _too_many_requests(retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Demasiados intentos. Inténtalo de nuevo más tarde.",
        headers={"Retry-After": str(retry_after)},
    )


@router.post("/register", response_model=RegisterAccepted, status_code=status.HTTP_202_ACCEPTED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> RegisterAccepted:
    ip = _client_ip(request)
    retry_after = register_limiter.retry_after(ip)
    if retry_after:
        raise _too_many_requests(retry_after)
    register_limiter.record(ip)

    # La respuesta es idéntica exista o no el correo, para no revelar qué cuentas están registradas.
    service.register(payload.email, payload.password)
    db.commit()
    return RegisterAccepted()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    ip = _client_ip(request)
    pair_key = f"{ip}|{payload.email}"
    retry_after = max(login_pair_limiter.retry_after(pair_key), login_ip_limiter.retry_after(ip))
    if retry_after:
        raise _too_many_requests(retry_after)

    try:
        token = service.login(payload.email, payload.password)
    except InvalidCredentials:
        login_pair_limiter.record(pair_key)
        login_ip_limiter.record(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except AccountDisabled:
        # La contraseña era correcta: se informa del estado de la cuenta sin contar el intento como fallo.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está pendiente de aprobación o desactivada.",
        ) from None
    login_pair_limiter.reset(pair_key)
    db.commit()  # persiste una eventual actualización del hash
    return token


@router.get("/me", response_model=UserRead)
def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    service.logout(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
