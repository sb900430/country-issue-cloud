import subprocess
import sys
from pathlib import Path


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
