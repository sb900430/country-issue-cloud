import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.batch.collection import CollectionRunner
from app.batch.collectors.fixture import FixtureCollector
from app.batch.collectors.rss import RssCollector, RssSource
from app.batch.deduplication import deduplicate_articles, normalize_title, normalize_url
from app.batch.models import CollectedArticle, CollectorKind
from app.core.settings import AppMode
from app.schemas.issues import CountryCode

WINDOW_END = datetime(2026, 8, 6, 0, 0, tzinfo=UTC)
WINDOW_START = WINDOW_END - timedelta(hours=24)


def article(
    article_id: str,
    country: CountryCode = CountryCode.US,
    title: str = "Market rises today",
    url: str = "https://example.com/story",
    summary: str | None = None,
    hours_ago: int = 1,
) -> CollectedArticle:
    return CollectedArticle(
        article_id=article_id,
        country=country,
        title=title,
        summary=summary,
        url=url,
        publisher="Example News",
        published_at=WINDOW_END - timedelta(hours=hours_ago),
    )


def test_fixture_collector_filters_country_window_and_limit(tmp_path: Path) -> None:
    payload = [
        article("inside").model_dump(mode="json"),
        article("other", country=CountryCode.JP).model_dump(mode="json"),
        article("old", hours_ago=25).model_dump(mode="json"),
    ]
    path = tmp_path / "articles.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = FixtureCollector("fixture-us", CountryCode.US, path).collect(
        WINDOW_START, WINDOW_END, 1
    )

    assert [item.article_id for item in result] == ["inside"]


def test_rss_collector_uses_injected_fetcher_without_network() -> None:
    feed = b"""<rss><channel><item><title>Local headline</title>
    <link>https://example.com/rss-story</link>
    <description>Summary</description><pubDate>Wed, 05 Aug 2026 23:00:00 GMT</pubDate>
    </item></channel></rss>"""
    requested: list[str] = []

    def fetch(url: str) -> bytes:
        requested.append(url)
        return feed

    source = RssSource("rss-us", CountryCode.US, "Example", "https://example.com/feed.xml")
    result = RssCollector(source, fetch).collect(WINDOW_START, WINDOW_END, 10)

    assert requested == [source.feed_url]
    assert result[0].title == "Local headline"


def test_feed_collector_supports_atom_and_skips_malformed_dates() -> None:
    feed = b"""<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><title>Broken item</title><link href="https://example.com/broken"/>
    <updated>not-a-date</updated></entry>
    <entry><title>METI release</title><link rel="alternate" href="https://example.com/meti"/>
    <summary>Official summary</summary><updated>2026-08-05T23:00:00Z</updated></entry>
    </feed>"""
    source = RssSource("meti", CountryCode.JP, "METI", "https://example.com/atom.xml")

    result = RssCollector(source, lambda _: feed).collect(WINDOW_START, WINDOW_END, 10)

    assert [item.title for item in result] == ["METI release"]
    assert result[0].summary == "Official summary"


def test_feed_collector_supports_dc_and_compact_dates_and_upgrades_links() -> None:
    feed = b"""<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>
    <item><title>DC date</title><link>http://example.com/dc</link>
    <dc:date>2026-08-05T01:00:00Z</dc:date></item>
    <item><title>Compact date</title><link>https://example.com/compact</link>
    <pubDate>20260805120000</pubDate></item>
    </channel></rss>"""
    source = RssSource("source", CountryCode.KR, "Publisher", "https://example.com/rss")

    result = RssCollector(source, lambda _: feed).collect(WINDOW_START, WINDOW_END, 10)

    assert len(result) == 2
    assert result[0].url == "https://example.com/dc"


def test_deduplication_applies_url_title_and_similarity_rules() -> None:
    articles = [
        article("a", url="https://EXAMPLE.com/story?utm_source=x&id=1"),
        article("b", url="https://example.com/story?id=1&fbclid=y", summary="more detail"),
        article("c", title="<b>MARKET rises today!</b>", url="https://example.com/c"),
        article("d", title="Market rises today now", url="https://example.com/d"),
    ]

    result = deduplicate_articles(articles)

    assert len(result) == 2
    assert result[0].article_id == "b"
    assert normalize_url(articles[0].url) == "https://example.com/story?id=1"
    assert normalize_title(articles[2].title) == "market rises today"


class StubCollector:
    def __init__(
        self,
        source_id: str,
        country: CountryCode,
        kind: CollectorKind,
        result: list[CollectedArticle] | Exception,
    ) -> None:
        self.source_id = source_id
        self.country = country
        self.kind = kind
        self.result = result
        self.thread_ids: list[int] = []

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]:
        self.thread_ids.append(threading.get_ident())
        if isinstance(self.result, Exception):
            raise self.result
        return self.result[:limit]


def test_runner_isolates_country_failures() -> None:
    us = StubCollector("us", CountryCode.US, CollectorKind.FIXTURE, RuntimeError("failed"))
    jp = StubCollector(
        "jp", CountryCode.JP, CollectorKind.FIXTURE, [article("jp", CountryCode.JP)]
    )
    runner = CollectionRunner([us, jp])

    result = runner.collect_all(
        (CountryCode.US, CountryCode.JP), WINDOW_START, WINDOW_END, AppMode.FIXTURE
    )

    assert result[CountryCode.US].errors == ("us:RuntimeError",)
    assert result[CountryCode.JP].articles[0].article_id == "jp"


def test_mixed_mode_falls_back_to_fixture_when_live_is_empty() -> None:
    live = StubCollector("live", CountryCode.KR, CollectorKind.LIVE, [])
    fixture = StubCollector(
        "fixture", CountryCode.KR, CollectorKind.FIXTURE, [article("kr", CountryCode.KR)]
    )

    result = CollectionRunner([live, fixture]).collect_all(
        (CountryCode.KR,), WINDOW_START, WINDOW_END, AppMode.MIXED
    )[CountryCode.KR]

    assert result.used_fixture_fallback is True
    assert result.articles[0].article_id == "kr"


def test_three_country_fixture_collection_uses_independent_results() -> None:
    fixture_path = Path(__file__).parents[2] / "sample-data" / "fixtures" / "articles.json"
    collectors = [
        FixtureCollector(f"fixture-{country.value.lower()}", country, fixture_path)
        for country in CountryCode
    ]

    result = CollectionRunner(collectors).collect_all(
        tuple(CountryCode), WINDOW_START, WINDOW_END, AppMode.FIXTURE
    )

    assert set(result) == set(CountryCode)
    assert all(len(country_result.articles) == 1 for country_result in result.values())
    assert all(
        country_result.articles[0].country == country
        for country, country_result in result.items()
    )
