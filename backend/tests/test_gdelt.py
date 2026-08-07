import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from app.batch.collectors.gdelt import GdeltCollector, GdeltSource, RequestIntervalGate
from app.schemas.issues import CountryCode

WINDOW_END = datetime(2026, 8, 7, 0, 0, tzinfo=UTC)
WINDOW_START = WINDOW_END - timedelta(hours=24)


def source(country: CountryCode = CountryCode.US) -> GdeltSource:
    return GdeltSource(
        source_id=f"gdelt-{country.value.lower()}",
        country=country,
        endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
        query="domain:example.com OR domain:business.example",
        query_version="test.v1",
        source_country="UnitedStates",
        source_language="English",
        allowed_domains=("example.com", "business.example"),
    )


def test_gdelt_collector_builds_bounded_query_and_maps_articles() -> None:
    requested: list[str] = []
    payload = {
        "articles": [
            {
                "url": "https://news.example.com/economy/1",
                "title": "Manufacturing investment expands",
                "seendate": "20260806T230000Z",
                "domain": "news.example.com",
                "language": "English",
                "sourcecountry": "United States",
            },
            {
                "url": "http://example.com/insecure",
                "title": "Insecure result",
                "seendate": "20260806T220000Z",
                "domain": "example.com",
            },
            {
                "url": "https://unapproved.example.net/story",
                "title": "Unapproved publisher",
                "seendate": "20260806T210000Z",
                "domain": "unapproved.example.net",
            },
            {"url": "https://example.com/missing-fields"},
            {
                "url": "https://example.com/wrong-country",
                "title": "Wrong country",
                "seendate": "20260806T200000Z",
                "domain": "example.com",
                "language": "English",
                "sourcecountry": "Japan",
            },
            {
                "url": "https://malicious.example.net/mismatch",
                "title": "Mismatched URL host",
                "seendate": "20260806T190000Z",
                "domain": "example.com",
                "language": "English",
                "sourcecountry": "United States",
            },
            {
                "url": "https://example.com/blank-title",
                "title": "   ",
                "seendate": "20260806T180000Z",
                "domain": "example.com",
            },
        ]
    }

    def fetch(url: str) -> bytes:
        requested.append(url)
        return json.dumps(payload).encode()

    result = GdeltCollector(source(), fetch).collect(WINDOW_START, WINDOW_END, 999)

    assert len(result) == 1
    assert result[0].publisher == "example.com"
    parameters = parse_qs(urlsplit(requested[0]).query)
    assert parameters["mode"] == ["artlist"]
    assert parameters["maxrecords"] == ["250"]
    assert parameters["startdatetime"] == ["20260806000000"]
    assert "sourcecountry:UnitedStates" in parameters["query"][0]


def test_gdelt_collector_skips_invalid_dates_and_outside_window() -> None:
    payload = {
        "articles": [
            {
                "url": "https://example.com/invalid",
                "title": "Invalid date",
                "seendate": "invalid",
                "domain": "example.com",
            },
            {
                "url": "https://example.com/old",
                "title": "Old article",
                "seendate": "20260801T000000Z",
                "domain": "example.com",
            },
        ]
    }

    result = GdeltCollector(source(), lambda _: json.dumps(payload).encode()).collect(
        WINDOW_START, WINDOW_END, 10
    )

    assert result == []


def test_gdelt_collector_rejects_malformed_response() -> None:
    with pytest.raises(ValueError, match="Invalid GDELT response"):
        GdeltCollector(source(), lambda _: b"not-json").collect(
            WINDOW_START, WINDOW_END, 10
        )


def test_gdelt_request_gate_waits_between_calls() -> None:
    clock_values = iter((0.0, 0.0, 2.0, 5.0))
    waits: list[float] = []
    gate = RequestIntervalGate(5.0, clock=lambda: next(clock_values), sleeper=waits.append)

    gate()
    gate()

    assert waits == [3.0]
