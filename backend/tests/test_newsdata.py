import json
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from app.batch.collectors.newsdata import NewsDataCollector, NewsDataSource
from app.batch.deduplication import deduplicate_articles, select_diverse_articles
from app.batch.newsdata_usage import (
    NewsDataUsageLedger,
    NewsDataUsageLimitExceededError,
    NewsDataUsagePolicy,
)
from app.schemas.issues import CountryCode

WINDOW_START = datetime(2026, 8, 7, tzinfo=UTC)
WINDOW_END = datetime(2026, 8, 9, tzinfo=UTC)


def source() -> NewsDataSource:
    return NewsDataSource(
        source_id="newsdata_us_business_news",
        country=CountryCode.US,
        endpoint="https://newsdata.io/api/1/latest",
        api_country="us",
        language="en",
        category="business",
        query_version="2026-08-08.v1",
        free_policy_review_due_at=date(2026, 9, 7),
    )


def test_newsdata_collector_paginates_filters_and_maps_articles(tmp_path: Path) -> None:
    requested: list[str] = []

    def fetch(url: str, headers: object) -> bytes:
        requested.append(url)
        assert headers == {"Accept": "application/json"}
        page = parse_qs(urlsplit(url).query).get("page")
        if not page:
            payload = {
                "status": "success",
                "nextPage": "next-token",
                "results": [
                    {
                        "article_id": "article-1",
                        "title": "  Markets   rise  ",
                        "link": "https://publisher.example/markets",
                        "pubDate": "2026-08-08 03:00:00",
                        "source_name": "Example Business",
                    },
                    {
                        "title": "Rejected URL",
                        "link": "http://publisher.example/plain",
                        "pubDate": "2026-08-08 03:00:00",
                    },
                ],
            }
        else:
            payload = {
                "status": "success",
                "results": [
                    {
                        "article_id": "article-2",
                        "title": "Central bank outlook",
                        "link": "https://another.example/outlook",
                        "pubDate": "2026-08-08T04:00:00Z",
                        "source_id": "another",
                    }
                ],
            }
        return json.dumps(payload).encode()

    collector = NewsDataCollector(
        source(),
        fetch,
        "test-api-key",
        NewsDataUsageLedger(tmp_path / "usage.json", NewsDataUsagePolicy()),
        today=lambda: date(2026, 8, 8),
    )

    articles = collector.collect(WINDOW_START, WINDOW_END, 2)

    assert [article.title for article in articles] == ["Markets rise", "Central bank outlook"]
    assert all(article.country is CountryCode.US for article in articles)
    assert len(requested) == 2
    first_parameters = parse_qs(urlsplit(requested[0]).query)
    assert first_parameters == {
        "apikey": ["test-api-key"],
        "country": ["us"],
        "language": ["en"],
        "category": ["business"],
        "size": ["10"],
    }
    assert parse_qs(urlsplit(requested[1]).query)["page"] == ["next-token"]
    assert collector.last_diagnostics["url_rejected"] == 1
    assert collector.last_diagnostics["accepted"] == 2


def test_newsdata_usage_ledger_stops_at_self_imposed_limit(tmp_path: Path) -> None:
    ledger = NewsDataUsageLedger(
        tmp_path / "usage.json",
        NewsDataUsagePolicy(daily_limit=2, monthly_limit=10),
        clock=lambda: datetime(2026, 8, 8, 9, tzinfo=UTC),
    )

    ledger.reserve_request()
    ledger.reserve_request()

    with pytest.raises(NewsDataUsageLimitExceededError, match="daily"):
        ledger.reserve_request()


def test_newsdata_collector_requires_policy_review_after_due_date(tmp_path: Path) -> None:
    collector = NewsDataCollector(
        source(),
        lambda _url, _headers: b"{}",
        "test-api-key",
        NewsDataUsageLedger(tmp_path / "usage.json", NewsDataUsagePolicy()),
        today=lambda: date(2026, 9, 8),
    )

    with pytest.raises(ValueError, match="policy review"):
        collector.collect(WINDOW_START, WINDOW_END, 10)


def test_newsdata_target_survives_deduplication_and_publisher_balance(tmp_path: Path) -> None:
    request_count = 0

    def fetch(_url: str, headers: object) -> bytes:
        nonlocal request_count
        assert headers == {"Accept": "application/json"}
        start = request_count * 10
        request_count += 1
        results = [
            {
                "article_id": f"article-{index}",
                "title": f"Business {sha256(str(index).encode()).hexdigest()}",
                "link": f"https://publisher-{index % 5}.example/article-{index}",
                "pubDate": "2026-08-08 03:00:00",
                "source_name": f"Publisher {index % 5}",
            }
            for index in range(start, start + 10)
        ]
        return json.dumps(
            {
                "status": "success",
                "results": results,
                "nextPage": f"page-{request_count}" if request_count < 15 else None,
            }
        ).encode()

    collector = NewsDataCollector(
        source(),
        fetch,
        "test-api-key",
        NewsDataUsageLedger(tmp_path / "usage.json", NewsDataUsagePolicy()),
        today=lambda: date(2026, 8, 8),
    )

    collected = collector.collect(WINDOW_START, WINDOW_END, 250)
    selected = select_diverse_articles(deduplicate_articles(collected), 250)

    assert len(collected) == 150
    assert len(selected) == 150
    assert request_count == 15
