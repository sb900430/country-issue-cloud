from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    naver_daily_request_limit: Literal[300] = 300
    naver_monthly_request_limit: Literal[9_000] = 9_000
    naver_usage_alert_threshold_1: Literal[50] = 50
    naver_usage_alert_threshold_2: Literal[80] = 80
    naver_paid_overage_enabled: Literal[False] = False
    bea_api_key: str | None = None
    e_stat_app_id: str | None = None
    llm_provider: str = "mock"
    llm_api_key: str | None = None
    llm_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
