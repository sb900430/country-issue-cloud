import json
from datetime import UTC, date, datetime
from pathlib import Path

from app.batch.collection_diagnostics import write_collection_diagnostics
from app.batch.models import CollectedArticle, CountryCollectionResult
from app.schemas.issues import CountryCode


def test_collection_diagnostics_contains_counts_without_article_content(tmp_path: Path) -> None:
    collected_at = datetime(2026, 8, 8, 0, tzinfo=UTC)
    article = CollectedArticle(
        article_id="secret-article-id",
        country=CountryCode.KR,
        title="민감한 원문 제목",
        url="https://example.com/private-story",
        publisher="Example",
        published_at=collected_at,
    )
    collections = {
        CountryCode.KR: CountryCollectionResult(
            country=CountryCode.KR,
            articles=(article,),
            errors=("naver:TimeoutError",),
            source_article_counts={"naver": 3, "rss": 0},
            source_filter_counts={
                "naver": {"response_items": 10, "domain_rejected": 7, "accepted": 3}
            },
            source_rejected_domain_counts={"naver": {"example.com": 7}},
            source_publisher_counts={"naver": {"Example": 3}},
            raw_article_count=3,
            deduplicated_article_count=2,
            collected_at=collected_at,
        )
    }
    path = tmp_path / "runtime" / "collection-diagnostics.json"

    write_collection_diagnostics(
        path,
        date(2026, 8, 8),
        datetime(2026, 8, 7, 0, tzinfo=UTC),
        collected_at,
        collections,
    )

    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert payload["countries"]["KR"] == {
        "deduplicated_article_count": 2,
        "errors": ["naver:TimeoutError"],
        "raw_article_count": 3,
        "selected_article_count": 1,
        "source_article_counts": {"naver": 3, "rss": 0},
        "source_filter_counts": {
            "naver": {"accepted": 3, "domain_rejected": 7, "response_items": 10}
        },
        "source_rejected_domain_counts": {"naver": {"example.com": 7}},
        "source_publisher_counts": {"naver": {"Example": 3}},
        "used_fixture_fallback": False,
    }
    assert "민감한 원문 제목" not in raw
    assert "private-story" not in raw
    assert "secret-article-id" not in raw
