import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch

from app.batch import cli


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
