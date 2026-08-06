from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.batch.issues import MockIssueExtractor
from app.batch.models import CountryCollectionResult
from app.batch.pipeline import IssuePipeline, PipelineLock, PipelineLockedError
from app.batch.publishing import StaticJsonPublisher
from app.repositories.json_issue_repository import JsonIssueRepository
from app.schemas.issues import CountryCode, IssueStatus
from tests.test_issues import make_article

TARGET_DATE = date(2026, 8, 6)


def collection(country: CountryCode, count: int) -> CountryCollectionResult:
    return CountryCollectionResult(
        country=country,
        articles=tuple(
            make_article(index, country, f"Issue {index % 5}") for index in range(count)
        ),
        collected_at=datetime.now(UTC),
    )


def test_pipeline_publishes_two_country_partial_success(tmp_path: Path) -> None:
    repository = JsonIssueRepository(tmp_path)
    pipeline = IssuePipeline(
        repository, MockIssueExtractor(), PipelineLock(tmp_path / "runtime" / "pipeline.lock")
    )

    result = pipeline.run(
        TARGET_DATE,
        {
            CountryCode.US: collection(CountryCode.US, 15),
            CountryCode.JP: collection(CountryCode.JP, 15),
        },
    )

    assert result.status == IssueStatus.PARTIAL_SUCCESS
    assert result.countries[CountryCode.KR].status == IssueStatus.FAILED
    assert repository.find_latest() == result


def test_pipeline_does_not_replace_latest_with_only_one_publishable_country(
    tmp_path: Path,
) -> None:
    repository = JsonIssueRepository(tmp_path)
    pipeline = IssuePipeline(repository, MockIssueExtractor(), PipelineLock(tmp_path / "lock"))

    result = pipeline.run(TARGET_DATE, {CountryCode.US: collection(CountryCode.US, 15)})

    assert result.status == IssueStatus.FAILED
    assert repository.find_latest() is None


def test_pipeline_dry_run_does_not_write_files(tmp_path: Path) -> None:
    repository = JsonIssueRepository(tmp_path)
    pipeline = IssuePipeline(repository, MockIssueExtractor(), PipelineLock(tmp_path / "lock"))
    collections = {country: collection(country, 30) for country in CountryCode}

    assert pipeline.run(TARGET_DATE, collections, dry_run=True).status == IssueStatus.SUCCESS
    assert repository.find_latest() is None


def test_pipeline_lock_rejects_duplicate_run_and_releases(tmp_path: Path) -> None:
    lock = PipelineLock(tmp_path / "runtime" / "pipeline.lock")
    with lock, pytest.raises(PipelineLockedError), PipelineLock(lock.path):
        pass
    assert not lock.path.exists()


def test_static_publisher_validates_and_outputs_public_json(tmp_path: Path) -> None:
    repository = JsonIssueRepository(tmp_path / "data")
    pipeline = IssuePipeline(
        repository, MockIssueExtractor(), PipelineLock(tmp_path / "runtime" / "lock")
    )
    pipeline.run(TARGET_DATE, {country: collection(country, 30) for country in CountryCode})
    site_data = tmp_path / "site" / "data" / "v1"

    outputs = StaticJsonPublisher(tmp_path / "data" / "published", site_data).publish()

    assert site_data / "latest.json" in outputs
    assert site_data / "2026-08-06.json" in outputs
    assert (site_data / "dates.json").read_text(encoding="utf-8").strip() == '[\n  "2026-08-06"\n]'


def test_static_publisher_keeps_existing_site_when_candidate_is_invalid(tmp_path: Path) -> None:
    published = tmp_path / "published"
    published.mkdir()
    (published / "latest.json").write_text("invalid", encoding="utf-8")
    site_data = tmp_path / "site" / "data" / "v1"
    site_data.mkdir(parents=True)
    (site_data / "latest.json").write_text("previous", encoding="utf-8")

    with pytest.raises(ValueError):
        StaticJsonPublisher(published, site_data).publish()
    assert (site_data / "latest.json").read_text(encoding="utf-8") == "previous"


def test_static_publisher_rolls_back_when_final_directory_swap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = JsonIssueRepository(tmp_path / "data")
    pipeline = IssuePipeline(
        repository, MockIssueExtractor(), PipelineLock(tmp_path / "runtime" / "lock")
    )
    pipeline.run(TARGET_DATE, {country: collection(country, 30) for country in CountryCode})
    site_data = tmp_path / "site" / "data" / "v1"
    site_data.mkdir(parents=True)
    (site_data / "marker.txt").write_text("previous", encoding="utf-8")
    original_replace = Path.replace

    def fail_candidate_swap(path: Path, target: Path) -> Path:
        if path.name == ".v1.tmp" and target == site_data:
            raise OSError("simulated directory swap failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_candidate_swap)

    with pytest.raises(OSError, match="simulated"):
        StaticJsonPublisher(tmp_path / "data" / "published", site_data).publish()
    assert (site_data / "marker.txt").read_text(encoding="utf-8") == "previous"
