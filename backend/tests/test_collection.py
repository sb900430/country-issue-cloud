import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.batch.collection import CollectionRunner
from app.batch.collectors.fixture import FixtureCollector
from app.batch.collectors.rss import RssCollector, RssSource
from app.batch.deduplication import (
    assign_story_clusters,
    canonical_publisher,
    deduplicate_articles,
    normalize_title,
    normalize_url,
    select_diverse_articles,
)
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


def test_rss_collector_retries_one_transient_malformed_xml_response() -> None:
    responses = iter(
        (
            b"<html>temporary gateway response",
            b"""<rss><channel><item><title>Recovered headline</title>
            <link>https://example.com/recovered</link>
            <pubDate>Wed, 05 Aug 2026 23:00:00 GMT</pubDate>
            </item></channel></rss>""",
        )
    )
    source = RssSource("rss-us", CountryCode.US, "Example", "https://example.com/feed.xml")

    result = RssCollector(source, lambda _url: next(responses)).collect(
        WINDOW_START, WINDOW_END, 10
    )

    assert [item.title for item in result] == ["Recovered headline"]


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


def test_feed_collector_supports_rss_one_rdf_items() -> None:
    feed = b"""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
    <channel rdf:about="https://example.com/feed"/>
    <item rdf:about="https://example.com/statistics">
      <title>Statistics release</title><link>https://example.com/statistics</link>
      <dc:date>2026-08-05</dc:date>
    </item></rdf:RDF>"""
    source = RssSource("statistics", CountryCode.JP, "Statistics", "https://example.com/rss")

    result = RssCollector(source, lambda _: feed).collect(WINDOW_START, WINDOW_END, 10)

    assert [item.title for item in result] == ["Statistics release"]
    assert result[0].published_at == datetime(2026, 8, 5, tzinfo=UTC)


def test_deduplication_removes_only_repeated_urls() -> None:
    articles = [
        article("a", url="https://EXAMPLE.com/story?utm_source=x&id=1"),
        article("b", url="https://example.com/story?id=1&fbclid=y", summary="more detail"),
        article("c", title="<b>MARKET rises today!</b>", url="https://example.com/c"),
        article("d", title="Market rises today now", url="https://example.com/d"),
    ]

    result = deduplicate_articles(articles)

    assert len(result) == 3
    assert result[0].article_id == "b"
    assert normalize_url(articles[0].url) == "https://example.com/story?id=1"
    assert normalize_title(articles[2].title) == "market rises today"


def test_diversity_weights_publishers_without_discarding_articles() -> None:
    articles = [
        article(
            f"publisher-a-{index}",
            title=f"Publisher A headline {index}",
            url=f"https://a.example/{index}",
        ).model_copy(update={"publisher": "Publisher A"})
        for index in range(40)
    ] + [
        article(
            f"publisher-{publisher}-{index}",
            title=f"Publisher {publisher} headline {index}",
            url=f"https://{publisher}.example/{index}",
        ).model_copy(update={"publisher": f"Publisher {publisher}"})
        for publisher in "BCDE"
        for index in range(15)
    ]

    selected = select_diverse_articles(articles, 100)

    assert len(selected) == 100
    assert sum(item.publisher == "Publisher A" for item in selected) == 40
    weighted_counts = {
        publisher: sum(
            item.ranking_weight
            for item in selected
            if canonical_publisher(item.publisher) == publisher
        )
        for publisher in {canonical_publisher(item.publisher) for item in selected}
    }
    assert max(weighted_counts.values()) <= len(selected) * 0.2


def test_diversity_groups_press_release_wire_aliases() -> None:
    articles = [
        article(
            f"wire-{index}",
            title=f"Wire headline {index}",
            url=f"https://wire.example/{index}",
        ).model_copy(update={"publisher": "Globe Newswire" if index % 2 else "PR Newswire"})
        for index in range(40)
    ] + [
        article(
            f"publisher-{publisher}-{index}",
            title=f"Publisher {publisher} headline {index}",
            url=f"https://{publisher}.example/{index}",
        ).model_copy(update={"publisher": f"Publisher {publisher}"})
        for publisher in "ABCDE"
        for index in range(12)
    ]

    selected = select_diverse_articles(articles, 100)

    wire_count = sum(
        canonical_publisher(item.publisher) == "press-release-wire" for item in selected
    )
    wire_weight = sum(
        item.ranking_weight
        for item in selected
        if canonical_publisher(item.publisher) == "press-release-wire"
    )
    assert wire_count == 40
    assert wire_weight == 20


def test_diversity_does_not_collapse_two_publisher_collection() -> None:
    articles = [
        article(
            f"major-{index}",
            title=f"Major publisher headline {index}",
            url=f"https://major.example/{index}",
        ).model_copy(update={"publisher": "Major Publisher"})
        for index in range(70)
    ] + [
        article(
            f"minor-{index}",
            title=f"Minor publisher headline {index}",
            url=f"https://minor.example/{index}",
        ).model_copy(update={"publisher": "Minor Publisher"})
        for index in range(30)
    ]

    selected = select_diverse_articles(articles, 100)

    assert len(selected) == 100
    assert sum(item.publisher == "Major Publisher" for item in selected) == 70
    assert sum(item.ranking_weight for item in selected) == 40


def test_story_clustering_preserves_syndicated_links_but_counts_one_story() -> None:
    articles = [
        article(
            "original",
            title="Louisiana pay raise deadline approaches for state workers - AP",
            url="https://first.example/news/2026/08/louisiana-pay-raise-deadline",
        ),
        article(
            "syndicated",
            title="Louisiana pay-raise deadline approaches for state workers",
            url="https://second.example/news/2026/08/louisiana-pay-raise-deadline",
            hours_ago=2,
        ),
        article(
            "separate",
            title="Federal Reserve reviews interest rate path",
            url="https://third.example/news/2026/08/federal-reserve-interest-rate",
        ),
    ]

    clustered = assign_story_clusters(articles)

    assert len(clustered) == 3
    assert clustered[0].story_cluster_id == clustered[1].story_cluster_id
    assert clustered[0].story_cluster_id != clustered[2].story_cluster_id


def test_story_clustering_requires_title_context_even_when_paths_match() -> None:
    articles = [
        article(
            "first",
            title="Federal Reserve reviews interest rate path",
            url="https://first.example/news/2026/08/shared-generic-article-path",
        ),
        article(
            "second",
            title="Space agency launches climate observation satellite",
            url="https://second.example/news/2026/08/shared-generic-article-path",
        ),
    ]

    clustered = assign_story_clusters(articles)

    assert clustered[0].story_cluster_id != clustered[1].story_cluster_id


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
    jp = StubCollector("jp", CountryCode.JP, CollectorKind.FIXTURE, [article("jp", CountryCode.JP)])
    runner = CollectionRunner([us, jp])

    result = runner.collect_all(
        (CountryCode.US, CountryCode.JP), WINDOW_START, WINDOW_END, AppMode.FIXTURE
    )

    assert result[CountryCode.US].errors == ("us:RuntimeError",)
    assert result[CountryCode.US].source_article_counts == {"us": 0}
    assert result[CountryCode.JP].articles[0].article_id == "jp"
    assert result[CountryCode.JP].source_article_counts == {"jp": 1}


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
    assert result.source_article_counts == {"live": 0, "fixture": 1}


def test_runner_reports_raw_deduplicated_and_selected_counts() -> None:
    repeated = article("duplicate", url="https://example.com/repeated")
    collector = StubCollector(
        "diagnostic-us",
        CountryCode.US,
        CollectorKind.LIVE,
        [repeated, repeated.model_copy(update={"article_id": "duplicate-copy"})],
    )

    result = CollectionRunner([collector]).collect_all(
        (CountryCode.US,), WINDOW_START, WINDOW_END, AppMode.LIVE
    )[CountryCode.US]

    assert result.source_article_counts == {"diagnostic-us": 2}
    assert result.source_publisher_counts == {"diagnostic-us": {"Example News": 2}}
    assert result.raw_article_count == 2
    assert result.deduplicated_article_count == 1
    assert result.story_cluster_count == 1
    assert result.diversity_weighted_article_count == 1
    assert len(result.articles) == 1


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
        country_result.articles[0].country == country for country, country_result in result.items()
    )
