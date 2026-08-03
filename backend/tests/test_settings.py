from pathlib import Path

from app.core.settings import AppMode, Settings


def test_fixture_mode_is_the_safe_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_mode is AppMode.FIXTURE
    assert settings.llm_provider == "mock"
    assert settings.news_api_key is None
    assert settings.llm_api_key is None


def test_environment_values_are_separated_from_source(monkeypatch: object) -> None:
    from pytest import MonkeyPatch

    assert isinstance(monkeypatch, MonkeyPatch)
    monkeypatch.setenv("APP_MODE", "mixed")
    monkeypatch.setenv("DATA_DIR", "runtime-data")

    settings = Settings(_env_file=None)

    assert settings.app_mode is AppMode.MIXED
    assert settings.data_dir == Path("runtime-data")
