from __future__ import annotations

from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "change_me"
    POSTGRES_DB: str = "civic_archive"

    DEBUG: bool = False
    PORT: int = 8000
    BOOTSTRAP_TABLES_ON_STARTUP: bool = False

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    REQUIRE_API_KEY: bool = False
    API_KEY: str | None = None
    RATE_LIMIT_PER_MINUTE: int = 0
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_METHODS: str = "GET,POST,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "*"
    ALLOWED_HOSTS: str = "*"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @staticmethod
    def _parse_csv(value: str) -> List[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def cors_allow_origins_list(self) -> List[str]:
        values = self._parse_csv(self.CORS_ALLOW_ORIGINS)
        return values or ["*"]

    @property
    def cors_allow_methods_list(self) -> List[str]:
        values = self._parse_csv(self.CORS_ALLOW_METHODS)
        return values or ["GET", "POST", "DELETE", "OPTIONS"]

    @property
    def cors_allow_headers_list(self) -> List[str]:
        values = self._parse_csv(self.CORS_ALLOW_HEADERS)
        return values or ["*"]

    @property
    def allowed_hosts_list(self) -> List[str]:
        values = self._parse_csv(self.ALLOWED_HOSTS)
        return values or ["*"]
