import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch

from app.batch import cli


def test_collection_window_uses_jst_day_end_for_historical_date() -> None:
    window_start, window_end = cli.resolve_collection_window(
        date(2026, 8, 7), datetime(2026, 8, 8, 6, tzinfo=UTC), 24
    )

    assert window_start == datetime(2026, 8, 6, 15, tzinfo=UTC)
    assert window_end == datetime(2026, 8, 7, 15, tzinfo=UTC)


def test_collection_window_caps_current_date_at_now() -> None:
    now = datetime(2026, 8, 8, 5, 30, tzinfo=UTC)

    window_start, window_end = cli.resolve_collection_window(date(2026, 8, 8), now, 24)

    assert window_start == datetime(2026, 8, 7, 5, 30, tzinfo=UTC)
    assert window_end == now


def test_publish_fixture_cli_builds_static_json(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    fixture = project_root / "sample-data" / "fixtures" / "issues_2026-08-03.json"
    data_dir = tmp_path / "data"
    site_dir = tmp_path / "site" / "data" / "v1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.batch.cli",
            "publish-fixture",
            "--fixture",
            str(fixture),
            "--data-dir",
            str(data_dir),
            "--site-data-dir",
            str(site_dir),
        ],
        cwd=project_root / "backend",
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "published 3 validated JSON files" in completed.stdout
    assert (site_dir / "latest.json").exists()
    assert (site_dir / "2026-08-03.json").exists()
    assert (site_dir / "dates.json").exists()


def test_publish_live_keeps_gdelt_disabled_without_explicit_flag(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "country-issue-cloud-batch",
            "publish-live",
            "--sources-config",
            str(tmp_path / "sources.yml"),
            "--data-dir",
            str(tmp_path / "data"),
            "--site-data-dir",
            str(tmp_path / "site"),
        ],
    )
    monkeypatch.setattr(cli, "load_rss_sources", lambda _path: [])
    monkeypatch.setattr(
        cli,
        "load_gdelt_sources",
        lambda _path: (_ for _ in ()).throw(AssertionError("GDELT must stay disabled")),
    )
    monkeypatch.setattr(
        cli,
        "load_naver_sources",
        lambda _path: (_ for _ in ()).throw(AssertionError("NAVER must stay disabled")),
    )
    captured: list[object] = []

    def run_live_batch(*arguments: object) -> object:
        captured.extend(arguments)
        return SimpleNamespace(status=SimpleNamespace(value="success"), countries={})

    monkeypatch.setattr(cli, "run_live_batch", run_live_batch)

    assert cli.main() == 0
    assert captured[1] == []
    assert captured[2] == []


def test_publish_keyword_live_can_skip_rss_for_historical_check(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "country-issue-cloud-batch",
            "publish-keyword-live",
            "--sources-config",
            str(tmp_path / "sources.yml"),
            "--data-dir",
            str(tmp_path / "data"),
            "--site-data-dir",
            str(tmp_path / "site"),
            "--target-date",
            "2026-08-07",
            "--skip-rss",
            "--single-attempt",
        ],
    )
    monkeypatch.setattr(
        cli,
        "load_rss_sources",
        lambda _path: (_ for _ in ()).throw(AssertionError("RSS must stay disabled")),
    )
    monkeypatch.setattr(cli, "load_gdelt_sources", lambda _path: [])
    monkeypatch.setattr(cli, "load_naver_sources", lambda _path: [])
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(naver_client_id=None, naver_client_secret=None),
    )
    captured: list[object] = []
    client_options: list[dict[str, object]] = []

    def create_client(**options: object) -> object:
        client_options.append(options)
        return SimpleNamespace(
            fetch=lambda _url: b"", fetch_with_headers=lambda _url, _headers: b""
        )

    monkeypatch.setattr(cli, "HttpsFeedClient", create_client)

    def run_live_keyword_batch(*arguments: object) -> object:
        captured.extend(arguments)
        return SimpleNamespace(status=SimpleNamespace(value="success"), countries={})

    monkeypatch.setattr(cli, "run_live_keyword_batch", run_live_keyword_batch)

    assert cli.main() == 0
    assert captured[0] == []
    assert client_options == [{"max_attempts": 1}]
