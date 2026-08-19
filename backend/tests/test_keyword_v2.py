import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.batch.keyword_fixture import publish_keyword_fixture
from app.batch.keyword_publishing import KeywordStaticJsonPublisher
from app.main import create_app
from app.repositories import JsonIssueRepository
from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.issues import CountryCode, IssueStatus
from app.schemas.keywords import CountryKeywordResult, KeywordResult

PROJECT_ROOT = Path(__file__).parents[2]


def test_keyword_fixture_publishes_schema_v2_with_related_articles(tmp_path: Path) -> None:
    site_dir = tmp_path / "site" / "data" / "v2"

    result = publish_keyword_fixture(
        PROJECT_ROOT / "sample-data" / "evaluation",
        tmp_path / "data",
        site_dir,
    )

    assert result.status is IssueStatus.SUCCESS
    assert all(result.countries[country].article_count == 120 for country in CountryCode)
    assert all(len(result.countries[country].top_keywords) == 5 for country in CountryCode)
    assert {keyword.label_ko for keyword in result.countries[CountryCode.US].top_keywords} == {
        "반도체",
        "금리",
        "달러 변동성",
        "기후",
        "주택",
    }
    assert {keyword.label_ko for keyword in result.countries[CountryCode.JP].top_keywords} == {
        "반도체",
        "금리",
        "엔화 변동성",
        "기후",
        "주택",
    }
    assert all(
        keyword.label_ko == keyword.label
        for keyword in result.countries[CountryCode.KR].top_keywords
    )
    assert all(
        len(keyword.related_articles) == 20
        for country in CountryCode
        for keyword in result.countries[country].top_keywords
    )
    published = KeywordResult.model_validate_json(
        (site_dir / "latest.json").read_text(encoding="utf-8")
    )
    assert published.schema_version == "2.0"
    assert (site_dir / "2026-08-07.json").exists()
    assert (site_dir / "dates.json").exists()
    status = json.loads((site_dir / "status.json").read_text(encoding="utf-8"))
    calendar = json.loads((site_dir / "calendar.json").read_text(encoding="utf-8"))
    assert status["attempted_date"] == "2026-08-07"
    assert status["displayed_date"] == "2026-08-07"
    assert status["countries"]["US"]["reason"] is None
    assert calendar["days"][0]["status"] == "success"
    stale_backup = site_dir.with_name(".v2.previous")
    stale_backup.mkdir()
    (stale_backup / "stale.json").write_text("{}", encoding="utf-8")
    outputs = KeywordStaticJsonPublisher(
        tmp_path / "data" / "keyword-published", site_dir
    ).publish()
    assert site_dir / "latest.json" in outputs
    assert not stale_backup.exists()


def test_schema_v2_accepts_previous_results_without_korean_labels(tmp_path: Path) -> None:
    result = publish_keyword_fixture(
        PROJECT_ROOT / "sample-data" / "evaluation",
        tmp_path / "data",
        tmp_path / "site" / "data" / "v2",
    )
    payload = result.model_dump(mode="json")
    for country in payload["countries"].values():
        for keyword in country["top_keywords"]:
            keyword.pop("label_ko")

    restored = KeywordResult.model_validate(payload)

    assert all(
        keyword.label_ko is None
        for country in restored.countries.values()
        for keyword in country.top_keywords
    )


def test_keyword_publisher_backfills_korean_labels_for_preserved_history(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    source_site = tmp_path / "source-site" / "data" / "v2"
    publish_keyword_fixture(
        PROJECT_ROOT / "sample-data" / "evaluation",
        data_dir,
        source_site,
    )
    published_dir = data_dir / "keyword-published"
    for path in published_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for country in payload["countries"].values():
            for keyword in country["top_keywords"]:
                keyword.pop("label_ko")
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    site_dir = tmp_path / "preserved-site" / "data" / "v2"
    KeywordStaticJsonPublisher(published_dir, site_dir).publish()
    restored = KeywordResult.model_validate_json(
        (site_dir / "latest.json").read_text(encoding="utf-8")
    )

    assert any(
        keyword.label_ko != keyword.label
        for keyword in restored.countries[CountryCode.US].top_keywords
    )
    assert any(
        keyword.label_ko != keyword.label
        for keyword in restored.countries[CountryCode.JP].top_keywords
    )
    assert all(
        keyword.label_ko == keyword.label
        for keyword in restored.countries[CountryCode.KR].top_keywords
    )


def test_v2_api_returns_published_keyword_data(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    publish_keyword_fixture(
        PROJECT_ROOT / "sample-data" / "evaluation",
        data_dir,
        tmp_path / "site" / "data" / "v2",
    )
    client = TestClient(
        create_app(
            repository=JsonIssueRepository(data_dir),
            keyword_repository=JsonKeywordRepository(
                data_dir, today_provider=lambda: date(2026, 8, 8)
            ),
            today_provider=lambda: date(2026, 8, 8),
        )
    )

    latest = client.get("/api/v2/keywords/latest")
    dates = client.get("/api/v2/keywords/dates")
    country = client.get("/api/v2/keywords/2026-08-07/KR")

    assert latest.status_code == 200
    assert latest.json()["schema_version"] == "2.0"
    assert dates.json() == ["2026-08-07"]
    assert country.status_code == 200
    assert len(country.json()["top_keywords"]) == 5


def test_v2_api_preserves_v1_and_rejects_invalid_country(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            repository=JsonIssueRepository(tmp_path),
            keyword_repository=JsonKeywordRepository(tmp_path),
            today_provider=lambda: date(2026, 8, 8),
        )
    )

    assert client.get("/api/v1/health").status_code == 200
    invalid = client.get("/api/v2/keywords/2026-08-07/GB")
    assert invalid.status_code == 400
    assert invalid.json()["detail"]["code"] == "invalid_country"


def test_keyword_publisher_restores_previous_site_when_swap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    site_dir = tmp_path / "site" / "data" / "v2"
    publish_keyword_fixture(PROJECT_ROOT / "sample-data" / "evaluation", data_dir, site_dir)
    previous = (site_dir / "latest.json").read_bytes()
    original_replace = Path.replace

    def fail_temporary_swap(path: Path, target: Path) -> Path:
        if path == site_dir.with_name(".v2.tmp") and target == site_dir:
            raise OSError("simulated atomic swap failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_temporary_swap)

    with pytest.raises(OSError, match="simulated atomic swap failure"):
        KeywordStaticJsonPublisher(data_dir / "keyword-published", site_dir).publish()

    assert (site_dir / "latest.json").read_bytes() == previous


def test_keyword_publisher_rejects_missing_or_orphan_latest(tmp_path: Path) -> None:
    publisher = KeywordStaticJsonPublisher(tmp_path / "missing", tmp_path / "site")
    with pytest.raises(FileNotFoundError):
        publisher.publish()

    data_dir = tmp_path / "data"
    site_dir = tmp_path / "published-site"
    publish_keyword_fixture(PROJECT_ROOT / "sample-data" / "evaluation", data_dir, site_dir)
    (data_dir / "keyword-published" / "keywords_2026-08-07.json").unlink()

    with pytest.raises(ValueError, match="no matching dated result"):
        KeywordStaticJsonPublisher(data_dir / "keyword-published", site_dir).publish()


def test_keyword_publisher_keeps_only_latest_seven_dates(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    site_dir = tmp_path / "site" / "data" / "v2"
    fixture = publish_keyword_fixture(
        PROJECT_ROOT / "sample-data" / "evaluation", data_dir, site_dir
    )
    repository = JsonKeywordRepository(data_dir)
    first_date = date(2026, 8, 1)

    for offset in range(8):
        target_date = first_date + timedelta(days=offset)
        repository.save(
            fixture.model_copy(
                update={
                    "date": target_date,
                    "generated_at": datetime.combine(
                        target_date, datetime.min.time(), tzinfo=UTC
                    ),
                }
            )
        )

    KeywordStaticJsonPublisher(
        data_dir / "keyword-published", site_dir
    ).publish()

    assert json.loads((site_dir / "dates.json").read_text(encoding="utf-8")) == [
        "2026-08-08",
        "2026-08-07",
        "2026-08-06",
        "2026-08-05",
        "2026-08-04",
        "2026-08-03",
        "2026-08-02",
    ]
    assert not (site_dir / "2026-08-01.json").exists()


def test_keyword_publisher_preserves_older_display_result_with_recent_failures(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    site_dir = tmp_path / "site" / "data" / "v2"
    fixture = publish_keyword_fixture(
        PROJECT_ROOT / "sample-data" / "evaluation", data_dir, site_dir
    )
    repository = JsonKeywordRepository(data_dir)
    displayed = fixture.model_copy(update={"date": date(2026, 8, 1)})
    repository.save(displayed)
    for day in range(2, 9):
        failed = KeywordResult(
            schema_version="2.0",
            date=date(2026, 8, day),
            generated_at=datetime(2026, 8, day, tzinfo=UTC),
            status=IssueStatus.FAILED,
            countries={
                country: CountryKeywordResult(
                    status=IssueStatus.FAILED,
                    article_count=0,
                    top_keywords=[],
                )
                for country in CountryCode
            },
        )
        repository.save_history(failed)

    KeywordStaticJsonPublisher(repository.published_dir, site_dir).publish()

    dates = json.loads((site_dir / "dates.json").read_text(encoding="utf-8"))
    status = json.loads((site_dir / "status.json").read_text(encoding="utf-8"))
    assert dates == [
        "2026-08-08",
        "2026-08-07",
        "2026-08-06",
        "2026-08-05",
        "2026-08-04",
        "2026-08-03",
        "2026-08-01",
    ]
    assert status["attempted_date"] == "2026-08-08"
    assert status["displayed_date"] == "2026-08-01"
