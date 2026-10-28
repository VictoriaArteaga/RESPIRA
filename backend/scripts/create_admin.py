"""Crea una cuenta administradora de forma interactiva.

Uso (desde backend/, con .env configurado y la migración de usuarios aplicada):
    python -m scripts.create_admin

La contraseña se pide por teclado (sin eco) y nunca se recibe por argumentos ni se imprime.
No existe ningún administrador predeterminado ni un endpoint público para crearlo.
"""
import sys
from getpass import getpass

from pydantic import ValidationError

from app.core.database import SessionLocal
from app.models.user import ROLE_ADMIN
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService, EmailAlreadyRegistered


def main() -> int:
    email = input("Correo del administrador: ").strip()
    password = getpass("Contraseña: ")
    if password != getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.", file=sys.stderr)
        return 1
    try:
        data = RegisterRequest(email=email, password=password)
    except ValidationError as error:
        for issue in error.errors():
            print(f"- {issue['loc'][-1]}: {issue['msg']}", file=sys.stderr)
        return 1

    with SessionLocal.begin() as db:
        try:
            user = AuthService(UserRepository(db)).create_user(data.email, data.password, ROLE_ADMIN, is_active=True)
        except EmailAlreadyRegistered:
            print("Ya existe una cuenta con ese correo.", file=sys.stderr)
            return 1
        print(f"Administrador creado: {user.email} (id {user.id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
