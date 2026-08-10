import json
from datetime import date, datetime
from pathlib import Path

from app.batch.models import CountryCollectionResult
from app.schemas.issues import CountryCode


def write_selected_article_export(
    path: Path,
    target_date: date,
    window_start: datetime,
    window_end: datetime,
    collections: dict[CountryCode, CountryCollectionResult],
) -> Path:
    payload = {
        "schema_version": "1.0",
        "target_date": target_date.isoformat(),
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "countries": {
            country.value: [
                {
                    "article_id": article.article_id,
                    "title": article.title,
                    "url": article.url,
                    "publisher": article.publisher,
                    "published_at": article.published_at.isoformat(),
                }
                for article in sorted(
                    result.articles,
                    key=lambda item: (-item.published_at.timestamp(), item.article_id),
                )
            ]
            for country, result in sorted(collections.items(), key=lambda item: item[0].value)
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary.replace(path)
    return path
