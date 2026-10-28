from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: SecretStr
    db_sslmode: str = "require"
    # Operaciones de arranque explícitas: nunca se ejecutan por defecto contra la base remota.
    db_create_tables: bool = False
    db_seed_simulated: bool = False
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("jwt_algorithm")
    @classmethod
    def _restrict_jwt_algorithm(cls, value: str) -> str:
        # Lista cerrada de algoritmos simétricos: evita "none" y la confusión entre claves públicas y secretos.
        if value not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM must be one of HS256, HS384, HS512.")
        return value

    @property
    def database_url(self) -> URL:
        # URL.create escapa los caracteres reservados de la contraseña y oculta el secreto en repr().
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"sslmode": self.db_sslmode},
        )


settings = Settings()
