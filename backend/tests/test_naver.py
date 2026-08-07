import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from app.batch.collectors.naver import NaverCollector, NaverSource
from app.batch.naver_usage import (
    NaverPaidOverageDisabledError,
    NaverUsageLedger,
    NaverUsagePolicy,
)

WINDOW_END = datetime(2026, 8, 7, 0, tzinfo=UTC)
WINDOW_START = WINDOW_END - timedelta(days=1)


def _source() -> NaverSource:
    return NaverSource(
        source_id="naver-kr",
        endpoint="https://naverapihub.apigw.ntruss.com/search/v1/news",
        queries=("경제", "금융"),
        query_version="test.v1",
        allowed_domains=("hankyung.com", "mk.co.kr"),
        free_policy_review_due_at=date(2099, 1, 1),
    )


def test_naver_collector_authenticates_filters_and_normalizes(tmp_path: Path) -> None:
    requested: list[str] = []
    payload = {
        "items": [
            {
                "title": "<b>반도체</b> 수출 &amp; 투자 확대",
                "originallink": "https://news.hankyung.com/economy/1",
                "pubDate": "Thu, 06 Aug 2026 23:00:00 +0000",
            },
            {
                "title": "허용되지 않은 기사",
                "originallink": "https://example.com/economy/2",
                "pubDate": "Thu, 06 Aug 2026 22:00:00 +0000",
            },
            {"title": "필드 누락"},
        ]
    }

    def fetch(url: str, headers: object) -> bytes:
        requested.append(url)
        assert "API-KEY-ID" in str(headers)
        return json.dumps(payload).encode()

    collector = NaverCollector(
        _source(),
        fetch,
        "client-id",
        "client-secret",
        NaverUsageLedger(tmp_path / "usage.json", NaverUsagePolicy()),
    )

    articles = collector.collect(WINDOW_START, WINDOW_END, 1)

    assert len(articles) == 1
    assert articles[0].title == "반도체 수출 & 투자 확대"
    assert articles[0].publisher == "hankyung.com"
    parameters = parse_qs(urlsplit(requested[0]).query)
    assert parameters["query"] == ["경제"]
    assert parameters["display"] == ["100"]


def test_naver_collector_cycles_queries_and_deduplicates_urls(tmp_path: Path) -> None:
    calls = 0

    def fetch(_url: str, _headers: object) -> bytes:
        nonlocal calls
        calls += 1
        return json.dumps(
            {
                "items": [
                    {
                        "title": f"경제 기사 {calls}",
                        "originallink": "https://www.mk.co.kr/news/economy/shared",
                        "pubDate": "Thu, 06 Aug 2026 23:00:00 +0000",
                    }
                ]
            }
        ).encode()

    articles = NaverCollector(
        _source(),
        fetch,
        "client-id",
        "client-secret",
        NaverUsageLedger(tmp_path / "usage.json", NaverUsagePolicy()),
    ).collect(WINDOW_START, WINDOW_END, 10)

    assert len(articles) == 1
    assert calls == 2


def test_naver_collector_caps_total_results_at_250(tmp_path: Path) -> None:
    source = NaverSource(
        source_id="naver-kr",
        endpoint="https://naverapihub.apigw.ntruss.com/search/v1/news",
        queries=("경제", "금융", "산업"),
        query_version="test.v1",
        allowed_domains=("mk.co.kr",),
        free_policy_review_due_at=date(2099, 1, 1),
    )
    call_index = 0

    def fetch(_url: str, _headers: object) -> bytes:
        nonlocal call_index
        call_index += 1
        return json.dumps(
            {
                "items": [
                    {
                        "title": f"경제 기사 {call_index}-{index}",
                        "originallink": (
                            f"https://www.mk.co.kr/news/economy/{call_index}-{index}"
                        ),
                        "pubDate": "Thu, 06 Aug 2026 23:00:00 +0000",
                    }
                    for index in range(100)
                ]
            }
        ).encode()

    articles = NaverCollector(
        source,
        fetch,
        "client-id",
        "client-secret",
        NaverUsageLedger(tmp_path / "usage.json", NaverUsagePolicy()),
    ).collect(WINDOW_START, WINDOW_END, 999)

    assert len(articles) == 250
    assert call_index == 3


def test_naver_collector_stops_before_request_when_free_policy_review_expires(
    tmp_path: Path,
) -> None:
    source = NaverSource(
        source_id="naver-kr",
        endpoint="https://naverapihub.apigw.ntruss.com/search/v1/news",
        queries=("경제",),
        query_version="test.v1",
        allowed_domains=("mk.co.kr",),
        free_policy_review_due_at=date(2026, 8, 6),
    )
    calls = 0

    def fetch(_url: str, _headers: object) -> bytes:
        nonlocal calls
        calls += 1
        return b'{"items":[]}'

    collector = NaverCollector(
        source,
        fetch,
        "client-id",
        "client-secret",
        NaverUsageLedger(tmp_path / "usage.json", NaverUsagePolicy()),
        today=lambda: date(2026, 8, 7),
    )

    with pytest.raises(NaverPaidOverageDisabledError, match="policy review"):
        collector.collect(WINDOW_START, WINDOW_END, 100)

    assert calls == 0
