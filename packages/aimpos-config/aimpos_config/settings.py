"""Runtime configuration loaded from the environment.

All environment access for the api and worker services flows through this module
(coding-standards.md §settings): no `os.getenv` scattered in application code.
Field names map to UPPER_SNAKE environment variables case-insensitively; the few
that diverge from a clean Python name declare an explicit ``validation_alias``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration sourced from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "aimpos-api"
    environment: str = "local"
    log_level: str = "INFO"

    # --- Auth (US-25) ---
    api_token: str = Field(default="change-me-local-dev-token", validation_alias="AIMPOS_API_TOKEN")

    # --- PostgreSQL (US-04) ---
    database_url: str = "postgresql+psycopg://aimpos:change-me@postgresql:5432/aimpos_spark"

    # --- MinIO (US-05) ---
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = Field(default="aimpos", validation_alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(
        default="change-me-local-dev-password", validation_alias="MINIO_ROOT_PASSWORD"
    )
    minio_bucket: str = "aimpos-hot-assets"
    minio_secure: bool = False

    # --- Redis ---
    redis_url: str = "redis://redis:6379/0"

    # --- Web / CORS (US-26) ---
    # Comma-separated list of allowed browser origins for the SPA.
    cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings (cached so the env is read once)."""
    return Settings()
