from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    provider_timeout_seconds: float = 12
    usgs_sync_seconds: int = 60
    eonet_sync_seconds: int = 900
    gdacs_sync_seconds: int = 900
    ai_provider: str = ""
    ai_model: str = "gpt-4.1-mini"
    ai_api_key: str = ""
    ai_timeout_seconds: float = 20
    ai_max_concurrent_requests: int = 4

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator(
        "provider_timeout_seconds",
        "usgs_sync_seconds",
        "eonet_sync_seconds",
        "gdacs_sync_seconds",
        "ai_timeout_seconds",
    )
    @classmethod
    def _positive_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("ai_max_concurrent_requests")
    @classmethod
    def _at_least_one(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

