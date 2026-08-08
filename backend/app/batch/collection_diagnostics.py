import json
from datetime import date, datetime
from pathlib import Path

from app.batch.models import CountryCollectionResult
from app.schemas.issues import CountryCode


def write_collection_diagnostics(
    path: Path,
    target_date: date,
    window_start: datetime,
    window_end: datetime,
    collections: dict[CountryCode, CountryCollectionResult],
) -> Path:
    payload = {
        "schema_version": "1.1",
        "target_date": target_date.isoformat(),
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "countries": {
            country.value: {
                "source_article_counts": dict(sorted(result.source_article_counts.items())),
                "source_filter_counts": {
                    source_id: dict(sorted(counts.items()))
                    for source_id, counts in sorted(result.source_filter_counts.items())
                },
                "source_rejected_domain_counts": {
                    source_id: dict(sorted(counts.items()))
                    for source_id, counts in sorted(
                        result.source_rejected_domain_counts.items()
                    )
                },
                "source_publisher_counts": {
                    source_id: dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
                    for source_id, counts in sorted(result.source_publisher_counts.items())
                },
                "raw_article_count": result.raw_article_count,
                "deduplicated_article_count": result.deduplicated_article_count,
                "selected_article_count": len(result.articles),
                "errors": list(result.errors),
                "used_fixture_fallback": result.used_fixture_fallback,
            }
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
