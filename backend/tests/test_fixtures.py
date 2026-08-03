from pathlib import Path

import pytest

from app.core.fixtures import load_issue_fixture

SAMPLE_FIXTURE = Path(__file__).parents[2] / "sample-data" / "fixtures" / "issues_2026-08-03.json"


def test_sample_fixture_contains_three_independent_countries() -> None:
    payload = load_issue_fixture(SAMPLE_FIXTURE)

    assert payload["schema_version"] == "1.0"
    assert set(payload["countries"]) == {"US", "JP", "KR"}


def test_fixture_loader_rejects_missing_fields(tmp_path: Path) -> None:
    invalid_fixture = tmp_path / "invalid.json"
    invalid_fixture.write_text('{"countries": {}}', encoding="utf-8")

    with pytest.raises(ValueError, match="missing required fields"):
        load_issue_fixture(invalid_fixture)
