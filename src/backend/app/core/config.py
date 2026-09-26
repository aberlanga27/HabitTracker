"""Application settings loaded from `HABITUDE_*` environment variables or `.env`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HABITUDE_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./habitude.db"
    session_ttl_days: int = 30
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
