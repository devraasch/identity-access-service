from __future__ import annotations

from functools import lru_cache

from pydantic import AnyUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="IAC_",
    )

    app_name: str = "identity-access-service"
    debug: bool = False
    database_url: AnyUrl

    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=24 * 60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=365)

    min_password_length: int = Field(default=8, ge=4, le=256)
    max_name_length: int = Field(default=255, ge=1, le=500)

    list_default_limit: int = Field(default=100, ge=1, le=10_000)
    list_max_limit: int = Field(default=500, ge=1, le=10_000)
    list_max_skip: int = Field(default=1_000_000, ge=0, le=100_000_000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
