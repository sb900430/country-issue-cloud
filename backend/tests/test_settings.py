from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.settings import AppMode, Settings


def test_fixture_mode_is_the_safe_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_mode is AppMode.FIXTURE
    assert settings.llm_provider == "mock"
    assert settings.news_api_key is None
    assert settings.newsdata_api_key is None
    assert settings.newsdata_daily_request_limit == 40
    assert settings.newsdata_monthly_request_limit == 1_200
    assert settings.newsdata_paid_overage_enabled is False
    assert settings.bea_api_key is None
    assert settings.e_stat_app_id is None
    assert settings.llm_api_key is None
    assert settings.naver_daily_request_limit == 300
    assert settings.naver_monthly_request_limit == 9_000
    assert settings.naver_usage_alert_threshold_1 == 50
    assert settings.naver_usage_alert_threshold_2 == 80
    assert settings.naver_paid_overage_enabled is False


def test_environment_values_are_separated_from_source(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("APP_MODE", "mixed")
    monkeypatch.setenv("DATA_DIR", "runtime-data")

    settings = Settings(_env_file=None)

    assert settings.app_mode is AppMode.MIXED
    assert settings.data_dir == Path("runtime-data")


def test_paid_naver_overage_cannot_be_enabled_by_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NAVER_PAID_OVERAGE_ENABLED", "true")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
