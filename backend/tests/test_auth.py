import uuid
from pathlib import Path
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateTable

from app.core.config import settings
from app.core.database import Base, SessionLocal
from app.core.security import TOKEN_ISSUER
from app.main import app
from app.models.user import ROLE_ADMIN, User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

PASSWORD = "Contrasena-segura-2025"
SECRET = settings.jwt_secret_key.get_secret_value()
PROTECTED_PATHS = [
    "/api/municipalities",
    "/api/cases",
    "/api/dashboard",
    "/api/alerts",
    "/api/risk-map",
    "/api/municipalities/1/risk",
]


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def new_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


def register(client: TestClient, email: str | None = None, password: str = PASSWORD):
    return client.post("/api/auth/register", json={"email": email or new_email(), "password": password})


def login(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def activate(email: str) -> None:
    with SessionLocal.begin() as db:
        user = UserRepository(db).get_by_email(email)
        assert user is not None
        user.is_active = True


def token_version_of(email: str) -> int:
    with SessionLocal() as db:
        user = UserRepository(db).get_by_email(email)
        assert user is not None
        return user.token_version


def analyst_token(client: TestClient) -> tuple[str, str]:
    email = new_email()
    assert register(client, email).status_code == 202
    activate(email)
    return email, login(client, email).json()["access_token"]


def admin_token(client: TestClient) -> tuple[int, str]:
    email = new_email()
    with SessionLocal.begin() as db:
        user = AuthService(UserRepository(db)).create_user(email, PASSWORD, ROLE_ADMIN, is_active=True)
        user_id = user.id
    return user_id, login(client, email).json()["access_token"]


def make_token(**overrides: object) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, object] = {
        "sub": "1",
        "tv": 0,
        "iss": TOKEN_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    payload.update(overrides)
    return jwt.encode({k: v for k, v in payload.items() if v is not None}, SECRET, algorithm="HS256")


# --- Registro ---------------------------------------------------------------------------------


def test_register_creates_inactive_analyst_without_exposing_secrets(client: TestClient) -> None:
    response = register(client, "  Persona.Nueva@Example.COM ")

    assert response.status_code == 202
    assert set(response.json()) == {"detail"}
    with SessionLocal() as db:
        user = UserRepository(db).get_by_email("persona.nueva@example.com")
        assert user is not None
        assert user.role == "analyst"
        assert user.is_active is False


def test_register_stores_argon2id_hash(client: TestClient) -> None:
    email = new_email()
    register(client, email)

    with SessionLocal() as db:
        user = UserRepository(db).get_by_email(email)
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash


def test_register_rejects_client_supplied_role(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register", json={"email": new_email(), "password": PASSWORD, "role": "admin"}
    )

    assert response.status_code == 422


def test_register_duplicate_email_is_indistinguishable_and_creates_no_second_account(client: TestClient) -> None:
    email = new_email()
    first = register(client, email)

    second = register(client, email.upper(), "Otra-contrasena-2025")

    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    with SessionLocal() as db:
        assert len([u for u in UserRepository(db).list_all() if u.email == email]) == 1
    activate(email)
    assert login(client, email).status_code == 200  # la contraseña original no fue reemplazada
    assert login(client, email, "Otra-contrasena-2025").status_code == 401


@pytest.mark.parametrize(
    "password",
    ["corta1", "sololetrassinnumero", "123456789012345", "x" * 129 + "1"],
)
def test_register_rejects_invalid_passwords(client: TestClient, password: str) -> None:
    assert register(client, new_email(), password).status_code == 422


def test_register_rejects_password_equal_to_email(client: TestClient) -> None:
    email = f"{uuid.uuid4().hex}1@example.com"

    assert register(client, email, email).status_code == 422


def test_register_rejects_invalid_email(client: TestClient) -> None:
    assert register(client, "no-es-un-correo").status_code == 422


# --- Inicio de sesión -------------------------------------------------------------------------


def test_login_returns_bearer_token(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    activate(email)

    response = login(client, email.upper())

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.access_token_expire_minutes * 60
    assert body["access_token"]


def test_login_failures_share_the_same_response(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    activate(email)

    wrong_password = login(client, email, "Otra-contrasena-9999")
    unknown_user = login(client, new_email())

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_pending_account_cannot_login_until_admin_approves(client: TestClient) -> None:
    email = new_email()
    register(client, email)

    pending = login(client, email)
    assert pending.status_code == 403
    assert "access_token" not in pending.json()

    _, token = admin_token(client)
    user_id = next(u["id"] for u in client.get("/api/admin/users", headers=auth(token)).json() if u["email"] == email)
    assert client.patch(f"/api/admin/users/{user_id}", json={"is_active": True}, headers=auth(token)).status_code == 200
    assert login(client, email).status_code == 200


def test_disabled_account_cannot_login(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    activate(email)
    _, token = admin_token(client)
    user_id = next(u["id"] for u in client.get("/api/admin/users", headers=auth(token)).json() if u["email"] == email)
    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(token))

    assert login(client, email).status_code == 403


def test_login_is_rate_limited_per_ip_and_email_and_recovers(client: TestClient) -> None:
    from app.core import rate_limit

    email = new_email()
    register(client, email)
    activate(email)

    for _ in range(5):
        assert login(client, email, "Incorrecta-9999-xx").status_code == 401
    blocked = login(client, email)  # incluso con la contraseña correcta
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert login(client, new_email()).status_code == 401  # otro correo no queda bloqueado

    rate_limit.login_pair_limiter.clear()  # el bloqueo es temporal, no permanente
    assert login(client, email).status_code == 200


def test_successful_login_resets_failure_counter(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    activate(email)

    for _ in range(4):
        login(client, email, "Incorrecta-9999-xx")
    assert login(client, email).status_code == 200
    for _ in range(4):
        assert login(client, email, "Incorrecta-9999-xx").status_code == 401


def test_register_is_rate_limited_per_ip(client: TestClient) -> None:
    statuses = [register(client).status_code for _ in range(11)]

    assert statuses[:10] == [202] * 10
    assert statuses[10] == 429


def test_attempt_limiter_window_expires() -> None:
    from app.core.rate_limit import AttemptLimiter

    now = [0.0]
    limiter = AttemptLimiter(max_attempts=2, window_seconds=60, clock=lambda: now[0])
    limiter.record("k")
    limiter.record("k")
    assert limiter.retry_after("k") > 0
    now[0] = 61.0
    assert limiter.retry_after("k") == 0


# --- Tokens -----------------------------------------------------------------------------------


def test_valid_token_returns_profile(client: TestClient) -> None:
    email, token = analyst_token(client)

    response = client.get("/api/auth/me", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["email"] == email


def test_missing_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_token_is_rejected(client: TestClient) -> None:
    token = make_token(exp=datetime.now(timezone.utc) - timedelta(minutes=1))

    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401


def test_tampered_token_is_rejected(client: TestClient) -> None:
    _, token = analyst_token(client)
    header, payload, signature = token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]

    assert client.get("/api/auth/me", headers=auth(f"{header}.{payload}.{flipped}")).status_code == 401


def test_token_signed_with_other_secret_is_rejected(client: TestClient) -> None:
    forged = jwt.encode(
        {"sub": "1", "tv": 0, "iss": TOKEN_ISSUER, "iat": datetime.now(timezone.utc),
         "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "otra-clave-completamente-distinta-0123456789",
        algorithm="HS256",
    )

    assert client.get("/api/auth/me", headers=auth(forged)).status_code == 401


def test_unsigned_token_is_rejected(client: TestClient) -> None:
    unsigned = jwt.encode(
        {"sub": "1", "tv": 0, "iss": TOKEN_ISSUER, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        None,
        algorithm="none",
    )

    assert client.get("/api/auth/me", headers=auth(unsigned)).status_code == 401


@pytest.mark.parametrize("claim", ["sub", "tv", "exp", "iat", "iss"])
def test_token_missing_required_claim_is_rejected(client: TestClient, claim: str) -> None:
    _, token = analyst_token(client)
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    del claims[claim]
    incomplete = jwt.encode(claims, SECRET, algorithm="HS256")

    assert client.get("/api/auth/me", headers=auth(incomplete)).status_code == 401


def test_token_signed_with_disallowed_algorithm_is_rejected(client: TestClient) -> None:
    _, token = analyst_token(client)
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    hs512 = jwt.encode(claims, SECRET, algorithm="HS512")

    assert client.get("/api/auth/me", headers=auth(hs512)).status_code == 401


def test_token_with_wrong_issuer_is_rejected(client: TestClient) -> None:
    assert client.get("/api/auth/me", headers=auth(make_token(iss="otro"))).status_code == 401


def test_token_for_deleted_user_is_rejected(client: TestClient) -> None:
    assert client.get("/api/auth/me", headers=auth(make_token(sub="999999"))).status_code == 401


# --- Endpoints protegidos y roles -------------------------------------------------------------


def test_health_remains_public(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize("path", PROTECTED_PATHS)
def test_epidemiological_endpoints_require_authentication(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401


def test_analyst_can_read_epidemiological_endpoints(client: TestClient) -> None:
    _, token = analyst_token(client)

    assert client.get("/api/municipalities", headers=auth(token)).status_code == 200
    assert client.get("/api/dashboard", headers=auth(token)).status_code == 200


def test_analyst_cannot_use_admin_endpoints(client: TestClient) -> None:
    _, token = analyst_token(client)

    assert client.get("/api/admin/users", headers=auth(token)).status_code == 403
    assert client.patch("/api/admin/users/1", json={"role": "admin"}, headers=auth(token)).status_code == 403


def test_admin_can_list_users_without_hashes(client: TestClient) -> None:
    _, token = admin_token(client)

    response = client.get("/api/admin/users", headers=auth(token))

    assert response.status_code == 200
    assert response.json()
    assert all("password_hash" not in user for user in response.json())


def test_admin_role_change_invalidates_existing_tokens(client: TestClient) -> None:
    email, user_token = analyst_token(client)
    _, token = admin_token(client)
    user_id = client.get("/api/auth/me", headers=auth(user_token)).json()["id"]

    response = client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=auth(token))

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert client.get("/api/auth/me", headers=auth(user_token)).status_code == 401
    new_token = login(client, email).json()["access_token"]
    assert client.get("/api/admin/users", headers=auth(new_token)).status_code == 200


def test_admin_rejects_unknown_role_and_extra_fields(client: TestClient) -> None:
    _, token = admin_token(client)

    assert client.patch("/api/admin/users/1", json={"role": "superuser"}, headers=auth(token)).status_code == 422
    assert client.patch("/api/admin/users/1", json={"email": "x@example.com"}, headers=auth(token)).status_code == 422


def test_admin_cannot_modify_own_account(client: TestClient) -> None:
    admin_id, token = admin_token(client)

    response = client.patch(f"/api/admin/users/{admin_id}", json={"is_active": False}, headers=auth(token))

    assert response.status_code == 400


def test_admin_update_unknown_user_returns_404(client: TestClient) -> None:
    _, token = admin_token(client)

    assert client.patch("/api/admin/users/999999", json={"is_active": False}, headers=auth(token)).status_code == 404


def test_deactivated_user_token_stops_working(client: TestClient) -> None:
    _, user_token = analyst_token(client)
    _, token = admin_token(client)
    user_id = client.get("/api/auth/me", headers=auth(user_token)).json()["id"]

    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(token))

    assert client.get("/api/auth/me", headers=auth(user_token)).status_code == 401


# --- Cierre de sesión -------------------------------------------------------------------------


def test_logout_revokes_the_token(client: TestClient) -> None:
    email, token = analyst_token(client)

    assert client.post("/api/auth/logout", headers=auth(token)).status_code == 204

    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
    assert client.get("/api/municipalities", headers=auth(token)).status_code == 401
    assert client.post("/api/auth/logout", headers=auth(token)).status_code == 401
    assert client.get("/api/auth/me", headers=auth(login(client, email).json()["access_token"])).status_code == 200


def test_logout_role_change_and_deactivation_increment_token_version(client: TestClient) -> None:
    email, token = analyst_token(client)
    _, admin = admin_token(client)
    user_id = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    version = token_version_of(email)

    client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=auth(admin))
    assert token_version_of(email) == version + 1
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401

    fresh = login(client, email).json()["access_token"]
    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(admin))
    assert token_version_of(email) == version + 2
    assert client.get("/api/auth/me", headers=auth(fresh)).status_code == 401

    client.patch(f"/api/admin/users/{user_id}", json={"is_active": True}, headers=auth(admin))
    again = login(client, email).json()["access_token"]
    client.post("/api/auth/logout", headers=auth(again))
    assert token_version_of(email) == version + 4
    assert client.get("/api/auth/me", headers=auth(again)).status_code == 401


def get_user_id(client: TestClient, admin: str, email: str) -> int:
    return next(u["id"] for u in client.get("/api/admin/users", headers=auth(admin)).json() if u["email"] == email)


def test_update_on_pending_account_does_not_touch_token_version_nor_allow_login(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    _, admin = admin_token(client)
    user_id = get_user_id(client, admin, email)

    assert client.patch(f"/api/admin/users/{user_id}", json={}, headers=auth(admin)).status_code == 200
    assert client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=auth(admin)).status_code == 200
    assert client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(admin)).status_code == 200

    assert token_version_of(email) == 0
    pending = login(client, email)
    assert pending.status_code == 403  # un rol admin no habilita el acceso de una cuenta inactiva
    assert "access_token" not in pending.json()


def test_approval_deactivation_and_reactivation_each_increment_token_version(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    _, admin = admin_token(client)
    user_id = get_user_id(client, admin, email)

    for expected_version, active in [(1, True), (2, False), (3, True)]:
        client.patch(f"/api/admin/users/{user_id}", json={"is_active": active}, headers=auth(admin))
        assert token_version_of(email) == expected_version


def test_disabled_account_role_change_keeps_token_version_and_stays_blocked(client: TestClient) -> None:
    email, token = analyst_token(client)
    _, admin = admin_token(client)
    user_id = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(admin))
    version = token_version_of(email)

    client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=auth(admin))

    assert token_version_of(email) == version
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
    assert login(client, email).status_code == 403


def test_noop_update_on_active_account_still_revokes_its_tokens(client: TestClient) -> None:
    email, token = analyst_token(client)
    _, admin = admin_token(client)
    user_id = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    version = token_version_of(email)

    client.patch(f"/api/admin/users/{user_id}", json={}, headers=auth(admin))

    assert token_version_of(email) == version + 1
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401


def test_logout_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/auth/logout").status_code == 401


# --- Integridad y compatibilidad con PostgreSQL ------------------------------------------------


def test_database_rejects_duplicate_email() -> None:
    email = new_email()
    with SessionLocal() as db:
        db.add(User(email=email, password_hash="x", role="analyst"))
        db.commit()
        db.add(User(email=email, password_hash="x", role="analyst"))
        with pytest.raises(IntegrityError):
            db.commit()


@pytest.mark.parametrize(
    "overrides",
    [{"role": "superuser"}, {"email": "MAYUSCULAS@EXAMPLE.COM"}],
    ids=["invalid-role", "uppercase-email"],
)
def test_database_rejects_invalid_user_rows(overrides: dict[str, str]) -> None:
    row = {"email": new_email(), "password_hash": "x", "role": "analyst", **overrides}
    with SessionLocal() as db:
        db.add(User(**row))
        with pytest.raises(IntegrityError):
            db.commit()


def test_users_table_compiles_for_postgresql() -> None:
    ddl = str(CreateTable(Base.metadata.tables["users"]).compile(dialect=postgresql.dialect()))

    assert "id SERIAL NOT NULL" in ddl
    assert "UNIQUE (email)" in ddl
    assert "ck_users_role_valid" in ddl and "ck_users_email_lowercase" in ddl
    assert "TIMESTAMP WITH TIME ZONE" in ddl


def test_alembic_has_a_single_head_after_user_migration() -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["0002"]
    assert script.get_revision("0002").down_revision == "0001"


# --- Estado derivado de cuentas (administración) ----------------------------------------------


def status_of(client: TestClient, admin: str, email: str) -> str:
    return next(u["status"] for u in client.get("/api/admin/users", headers=auth(admin)).json() if u["email"] == email)


def test_user_status_is_pending_active_or_disabled(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    _, admin = admin_token(client)

    def status_of() -> str:
        return next(u["status"] for u in client.get("/api/admin/users", headers=auth(admin)).json() if u["email"] == email)

    user_id = next(u["id"] for u in client.get("/api/admin/users", headers=auth(admin)).json() if u["email"] == email)
    assert status_of() == "pending"
    client.patch(f"/api/admin/users/{user_id}", json={"is_active": True}, headers=auth(admin))
    assert status_of() == "active"
    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(admin))
    assert status_of() == "disabled"
    client.patch(f"/api/admin/users/{user_id}", json={"is_active": True}, headers=auth(admin))
    assert status_of() == "active"  # la reactivación está soportada


def test_admin_endpoints_reject_missing_token_and_expose_no_secrets(client: TestClient) -> None:
    assert client.get("/api/admin/users").status_code == 401
    assert client.patch("/api/admin/users/1", json={"is_active": True}).status_code == 401
    _, admin = admin_token(client)
    body = client.get("/api/admin/users", headers=auth(admin)).text
    assert "password" not in body and "token" not in body and "$argon2" not in body


def test_status_pending_survives_noop_and_role_updates(client: TestClient) -> None:
    email = new_email()
    register(client, email)
    _, admin = admin_token(client)
    user_id = get_user_id(client, admin, email)

    client.patch(f"/api/admin/users/{user_id}", json={}, headers=auth(admin))
    assert status_of(client, admin, email) == "pending"
    client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=auth(admin))
    assert status_of(client, admin, email) == "pending"


def test_status_of_explicitly_rejected_pending_account_stays_pending(client: TestClient) -> None:
    # Limitación conocida de no tener un campo explícito de aprobación: no existe el estado "rechazada".
    email = new_email()
    register(client, email)
    _, admin = admin_token(client)
    user_id = get_user_id(client, admin, email)

    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(admin))

    assert status_of(client, admin, email) == "pending"


def test_status_of_disabled_account_survives_role_updates(client: TestClient) -> None:
    email, token = analyst_token(client)
    _, admin = admin_token(client)
    user_id = client.get("/api/auth/me", headers=auth(token)).json()["id"]

    client.patch(f"/api/admin/users/{user_id}", json={"is_active": False}, headers=auth(admin))
    client.patch(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=auth(admin))

    assert status_of(client, admin, email) == "disabled"


# --- Script del primer administrador y configuración -------------------------------------------


def run_create_admin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], email: str, *passwords: str):
    from scripts import create_admin

    monkeypatch.setattr("builtins.input", lambda _prompt="": email)
    answers = iter(passwords)
    monkeypatch.setattr(create_admin, "getpass", lambda _prompt="": next(answers))
    code = create_admin.main()
    return code, capsys.readouterr()


def test_create_admin_script_creates_active_admin_without_echoing_password(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    email = new_email()

    code, output = run_create_admin(monkeypatch, capsys, email, PASSWORD, PASSWORD)

    assert code == 0
    assert PASSWORD not in output.out + output.err
    with SessionLocal() as db:
        user = UserRepository(db).get_by_email(email)
        assert user is not None and user.role == "admin" and user.is_active is True
        assert user.password_hash.startswith("$argon2id$")


@pytest.mark.parametrize("password", ["corta1", "sololetrassinnumero", "123456789012345"])
def test_create_admin_script_rejects_weak_passwords(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], password: str
) -> None:
    email = new_email()

    code, output = run_create_admin(monkeypatch, capsys, email, password, password)

    assert code == 1
    assert password not in output.out + output.err
    with SessionLocal() as db:
        assert UserRepository(db).get_by_email(email) is None


def test_create_admin_script_rejects_mismatch_invalid_email_and_duplicates(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_create_admin(monkeypatch, capsys, new_email(), PASSWORD, PASSWORD + "x")[0] == 1
    assert run_create_admin(monkeypatch, capsys, "no-es-correo", PASSWORD, PASSWORD)[0] == 1
    email = new_email()
    assert run_create_admin(monkeypatch, capsys, email, PASSWORD, PASSWORD)[0] == 0
    assert run_create_admin(monkeypatch, capsys, email, PASSWORD, PASSWORD)[0] == 1


def test_no_public_endpoint_creates_admins(client: TestClient) -> None:
    for path in ["/api/admin/users", "/api/auth/admin", "/api/auth/register/admin"]:
        response = client.post(path, json={"email": new_email(), "password": PASSWORD})
        assert response.status_code in {401, 404, 405}


def test_jwt_secret_is_required_and_has_no_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import ValidationError

    from app.core.config import Settings

    monkeypatch.delenv("JWT_SECRET_KEY")
    with pytest.raises(ValidationError, match="jwt_secret_key"):
        Settings(_env_file=None)
    monkeypatch.setenv("JWT_SECRET_KEY", "demasiado-corta")
    with pytest.raises(ValidationError, match="jwt_secret_key"):
        Settings(_env_file=None)
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("JWT_ALGORITHM", "none")
    with pytest.raises(ValidationError, match="HS256"):
        Settings(_env_file=None)
