from sqlalchemy.exc import IntegrityError

from app.core.security import (
    burn_password_check,
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.models.user import ROLE_ANALYST, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserAdminUpdate


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class AccountDisabled(Exception):
    pass


class UserNotFound(Exception):
    pass


class ForbiddenSelfChange(Exception):
    pass


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def register(self, email: str, password: str) -> None:
        """Solicitud de cuenta: el rol nunca proviene del cliente y la cuenta queda pendiente de aprobación.

        Si el correo ya existe no se informa: el resultado es indistinguible para quien solicita (sin enumeración).
        """
        try:
            self.create_user(email, password, ROLE_ANALYST, is_active=False)
        except EmailAlreadyRegistered:
            hash_password(password)  # iguala el coste de cómputo con una solicitud nueva

    def create_user(self, email: str, password: str, role: str, is_active: bool = False) -> User:
        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyRegistered
        user = User(
            email=email, password_hash=hash_password(password), role=role, is_active=is_active, token_version=0
        )
        try:
            with self.users.db.begin_nested():
                self.users.add(user)
        except IntegrityError as error:  # carrera entre dos registros: decide la restricción UNIQUE
            raise EmailAlreadyRegistered from error
        return user

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.users.get_by_email(email)
        if user is None:
            burn_password_check(password)
            raise InvalidCredentials
        if not verify_password(user.password_hash, password):
            raise InvalidCredentials
        if not user.is_active:
            raise AccountDisabled
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        token, expires_in = create_access_token(user.id, user.token_version)
        return TokenResponse(access_token=token, expires_in=expires_in)

    def logout(self, user: User) -> None:
        user.token_version += 1

    def list_users(self) -> list[User]:
        return self.users.list_all()

    def update_user(self, acting_admin: User, user_id: int, changes: UserAdminUpdate) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise UserNotFound
        if user.id == acting_admin.id:
            # Evita que el último administrador se degrade o se desactive por error.
            raise ForbiddenSelfChange
        was_active = user.is_active
        if changes.role is not None:
            user.role = changes.role
        if changes.is_active is not None:
            user.is_active = changes.is_active
        # Solo hay tokens que revocar si la cuenta estaba o queda activa. Una cuenta inactiva no puede iniciar
        # sesión ni usar tokens (get_current_user la rechaza), así que no se incrementa: de lo contrario un PATCH
        # sin efecto o un cambio de rol sobre una cuenta pendiente la haría pasar por "desactivada".
        if was_active or user.is_active:
            user.token_version += 1
        return user
