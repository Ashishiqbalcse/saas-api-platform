from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/saasdb"
    redis_url: str = "redis://localhost:6379/0"

    api_key_pepper: str = Field("dev-pepper-change-me", min_length=12)
    jwt_secret: str = Field("dev-jwt-secret-change-me", min_length=12)

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""
    stripe_price_enterprise: str = ""
    stripe_test_mode: bool = True

    disable_rate_limit: bool = False
    usage_log_inline: bool = False
    auth_cache_ttl_seconds: int = 60

    public_paths: tuple[str, ...] = (
        "/",
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/tenants/register",
        "/api/billing/webhook",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
