from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMode(StrEnum):
    FIXTURE = "fixture"
    LIVE = "live"
    MIXED = "mixed"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_mode: AppMode = AppMode.FIXTURE
    api_prefix: str = Field(default="/api/v1", pattern=r"^/api/v[0-9]+$")
    service_timezone: str = "Asia/Tokyo"
    data_dir: Path = Path("../data")
    news_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    llm_provider: str = "mock"
    llm_api_key: str | None = None
    llm_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
