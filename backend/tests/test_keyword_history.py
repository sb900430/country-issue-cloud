from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.batch.keyword_history import restore_keyword_history
from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.issues import CountryCode, IssueStatus
from app.schemas.keywords import CountryKeywordResult, KeywordResult


def _result(value: date) -> KeywordResult:
    return KeywordResult(
        schema_version="2.0",
        date=value,
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
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


def test_restore_keyword_history_imports_only_previous_six_dates(tmp_path: Path) -> None:
    dates = [date(2026, 8, day) for day in range(3, 10)]
    payloads = {
        "https://example.com/data/v2/dates.json": (
            b'["2026-08-09","2026-08-08","2026-08-07","2026-08-06",'
            b'"2026-08-05","2026-08-04","2026-08-03"]'
        ),
        **{
            f"https://example.com/data/v2/{value.isoformat()}.json": _result(
                value
            ).model_dump_json().encode()
            for value in dates
        },
    }
    repository = JsonKeywordRepository(
        tmp_path, today_provider=lambda: date(2026, 8, 10)
    )

    restored = restore_keyword_history(
        "https://example.com/data/v2/",
        repository,
        date(2026, 8, 10),
        payloads.__getitem__,
    )

    assert restored == [date(2026, 8, day) for day in range(9, 3, -1)]
    assert repository.find_available_dates(7) == [
        date(2026, 8, day) for day in range(9, 3, -1)
    ]
    assert sorted(repository.published_dir.glob("keywords_*.json"))
    assert not (repository.published_dir / "latest.json").exists()


def test_restore_keyword_history_rejects_mismatched_payload(tmp_path: Path) -> None:
    payloads = {
        "https://example.com/data/v2/dates.json": b'["2026-08-09"]',
        "https://example.com/data/v2/2026-08-09.json": _result(
            date(2026, 8, 8)
        ).model_dump_json().encode(),
    }

    with pytest.raises(ValueError, match="Mismatched"):
        restore_keyword_history(
            "https://example.com/data/v2",
            JsonKeywordRepository(tmp_path),
            date(2026, 8, 10),
            payloads.__getitem__,
        )


def test_restore_keyword_history_can_preserve_current_latest_for_main_push(
    tmp_path: Path,
) -> None:
    current = _result(date(2026, 8, 10))
    previous = _result(date(2026, 8, 9))
    payloads = {
        "https://example.com/data/v2/latest.json": current.model_dump_json().encode(),
        "https://example.com/data/v2/dates.json": b'["2026-08-10","2026-08-09"]',
        "https://example.com/data/v2/2026-08-09.json": previous.model_dump_json().encode(),
    }
    repository = JsonKeywordRepository(
        tmp_path, today_provider=lambda: date(2026, 8, 10)
    )

    restored = restore_keyword_history(
        "https://example.com/data/v2",
        repository,
        date(2026, 8, 10),
        payloads.__getitem__,
        include_latest=True,
    )

    assert restored == [date(2026, 8, 10), date(2026, 8, 9)]
    assert repository.find_latest() == current
    assert repository.find_by_date(date(2026, 8, 9)) == previous
