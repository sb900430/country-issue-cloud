import json
from datetime import UTC, date, datetime
from pathlib import Path

from app.batch.admin_export import write_selected_article_export
from app.batch.models import CollectedArticle, CountryCollectionResult
from app.schemas.issues import CountryCode


def test_selected_article_export_contains_public_metadata_for_admin_review(
    tmp_path: Path,
) -> None:
    published_at = datetime(2026, 8, 10, 0, tzinfo=UTC)
    article = CollectedArticle(
        article_id="article-id",
        country=CountryCode.KR,
        title="반도체 수출 증가",
        url="https://example.com/article",
        publisher="Example News",
        published_at=published_at,
    )
    collections = {
        CountryCode.KR: CountryCollectionResult(
            country=CountryCode.KR,
            articles=(article,),
            collected_at=published_at,
        )
    }

    path = write_selected_article_export(
        tmp_path / "runtime" / "admin" / "selected-articles.json",
        date(2026, 8, 10),
        published_at,
        published_at,
        collections,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["countries"]["KR"] == [
        {
            "article_id": "article-id",
            "title": "반도체 수출 증가",
            "url": "https://example.com/article",
            "publisher": "Example News",
            "published_at": "2026-08-10T00:00:00+00:00",
        }
    ]
