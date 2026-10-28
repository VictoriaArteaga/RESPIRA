from pydantic import SecretStr
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
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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
