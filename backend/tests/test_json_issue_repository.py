from datetime import date
from pathlib import Path
from shutil import copyfile

import pytest

from app.repositories import JsonIssueRepository, RepositoryDataError
from app.schemas.issues import IssueResult, IssueStatus

SAMPLE_FIXTURE = Path(__file__).parents[2] / "sample-data" / "fixtures" / "issues_2026-08-03.json"


def create_repository(tmp_path: Path) -> JsonIssueRepository:
    return JsonIssueRepository(tmp_path, today_provider=lambda: date(2026, 8, 4))


def load_sample_result() -> IssueResult:
    return IssueResult.model_validate_json(SAMPLE_FIXTURE.read_text(encoding="utf-8"))


def test_find_by_date_returns_validated_result(tmp_path: Path) -> None:
    published_dir = tmp_path / "published"
    published_dir.mkdir()
    copyfile(SAMPLE_FIXTURE, published_dir / "issues_2026-08-03.json")

    result = create_repository(tmp_path).find_by_date(date(2026, 8, 3))

    assert result is not None
    assert result.date == date(2026, 8, 3)


def test_find_by_date_returns_none_when_file_is_absent(tmp_path: Path) -> None:
    result = create_repository(tmp_path).find_by_date(date(2026, 8, 3))

    assert result is None


def test_find_latest_raises_for_corrupt_data(tmp_path: Path) -> None:
    published_dir = tmp_path / "published"
    published_dir.mkdir()
    (published_dir / "latest.json").write_text("not-json", encoding="utf-8")

    with pytest.raises(RepositoryDataError, match="latest.json"):
        create_repository(tmp_path).find_latest()


def test_find_available_dates_filters_range_and_ignores_unknown_files(tmp_path: Path) -> None:
    published_dir = tmp_path / "published"
    published_dir.mkdir()
    for name in (
        "issues_2026-08-04.json",
        "issues_2026-08-03.json",
        "issues_2026-07-27.json",
        "issues_invalid.json",
        "latest.json",
    ):
        (published_dir / name).touch()

    result = create_repository(tmp_path).find_available_dates(within_days=7)

    assert result == [date(2026, 8, 4), date(2026, 8, 3)]


def test_find_available_dates_rejects_non_positive_range(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        create_repository(tmp_path).find_available_dates(within_days=0)


def test_save_atomically_publishes_dated_and_latest_files(tmp_path: Path) -> None:
    repository = create_repository(tmp_path)

    repository.save(load_sample_result())

    assert repository.find_by_date(date(2026, 8, 3)) == load_sample_result()
    assert repository.find_latest() == load_sample_result()
    assert not list((tmp_path / "published").glob("*.tmp"))


def test_save_replaces_existing_result(tmp_path: Path) -> None:
    repository = create_repository(tmp_path)
    result = load_sample_result()
    repository.save(result)
    updated = result.model_copy(update={"status": IssueStatus.PARTIAL_SUCCESS})

    repository.save(updated)

    assert repository.find_latest() == updated


def test_delete_expired_keeps_today_and_previous_six_days(tmp_path: Path) -> None:
    published_dir = tmp_path / "published"
    published_dir.mkdir()
    for published_date in (date(2026, 8, 4), date(2026, 7, 29), date(2026, 7, 28)):
        (published_dir / f"issues_{published_date.isoformat()}.json").touch()
    (published_dir / "latest.json").touch()

    deleted_count = create_repository(tmp_path).delete_expired(retention_days=7)

    assert deleted_count == 1
    assert (published_dir / "issues_2026-07-29.json").exists()
    assert not (published_dir / "issues_2026-07-28.json").exists()
    assert (published_dir / "latest.json").exists()


def test_delete_expired_rejects_non_positive_retention(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        create_repository(tmp_path).delete_expired(retention_days=0)
