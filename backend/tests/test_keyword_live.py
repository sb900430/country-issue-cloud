from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path

from app.batch.collectors.rss import RssSource
from app.batch.live import run_live_keyword_batch
from app.schemas.issues import CountryCode, IssueStatus

TOPICS = {
    CountryCode.US: (
        "semiconductor investment expands",
        "interest rate outlook changes",
        "dollar volatility increases",
        "climate policy affects markets",
        "housing demand slows",
    ),
    CountryCode.JP: (
        "半導体投資が拡大",
        "政策金利の見通し変化",
        "円相場の変動性が上昇",
        "気候政策が市場に影響",
        "住宅需要が減速",
    ),
    CountryCode.KR: (
        "반도체 투자 확대",
        "기준금리 전망 변화",
        "원화 변동성 상승",
        "기후 정책 시장 영향",
        "주택 수요 둔화",
    ),
}


def _feed(
    country: CountryCode, source_index: int, published_at: datetime, count: int = 20
) -> bytes:
    items = ""
    for index in range(count):
        suffix = sha256(f"{country}:{source_index}:{index}".encode()).hexdigest()[:24]
        items += (
            f"<item><title>{TOPICS[country][index % 5]} {suffix}</title>"
            f"<link>https://example.com/{country.value}/{source_index}/{index}</link>"
            f"<pubDate>{published_at.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate></item>"
        )
    return f"<rss><channel>{items}</channel></rss>".encode()


def test_live_keyword_batch_publishes_three_country_top_five(tmp_path: Path) -> None:
    end = datetime(2026, 8, 8, 0, tzinfo=UTC)
    sources = [
        RssSource(
            source_id=f"{country.value}-{index}",
            country=country,
            publisher=f"{country.value} Publisher {index}",
            feed_url=f"https://example.com/{country.value}/{index}.xml",
            include_summary=False,
        )
        for country in CountryCode
        for index in range(5)
    ]
    payloads = {
        source.feed_url: _feed(source.country, index % 5, end - timedelta(hours=1))
        for index, source in enumerate(sources)
    }

    result = run_live_keyword_batch(
        sources,
        [],
        [],
        [],
        payloads.__getitem__,
        lambda _url, _headers: b"{}",
        None,
        None,
        None,
        end - timedelta(hours=24),
        end,
        end.date(),
        tmp_path / "data",
        tmp_path / "site" / "data" / "v2",
    )

    assert result.status is IssueStatus.SUCCESS
    assert all(result.countries[country].article_count == 100 for country in CountryCode)
    assert all(len(result.countries[country].top_keywords) == 5 for country in CountryCode)
    assert (tmp_path / "site" / "data" / "v2" / "latest.json").exists()
    assert (tmp_path / "data" / "runtime" / "admin" / "selected-articles.json").exists()


def test_live_keyword_batch_publishes_at_fifty_articles_per_country(
    tmp_path: Path,
) -> None:
    end = datetime(2026, 8, 9, 0, tzinfo=UTC)
    sources = [
        RssSource(
            source_id=f"{country.value}-{index}",
            country=country,
            publisher=f"{country.value} Publisher {index}",
            feed_url=f"https://example.com/{country.value}/{index}.xml",
            include_summary=False,
        )
        for country in CountryCode
        for index in range(5)
    ]
    payloads = {
        source.feed_url: _feed(
            source.country, index % 5, end - timedelta(hours=1), count=10
        )
        for index, source in enumerate(sources)
    }
    site_dir = tmp_path / "site" / "data" / "v2"

    result = run_live_keyword_batch(
        sources,
        [],
        [],
        [],
        payloads.__getitem__,
        lambda _url, _headers: b"{}",
        None,
        None,
        None,
        end - timedelta(hours=24),
        end,
        end.date(),
        tmp_path / "data",
        site_dir,
    )

    assert result.status is IssueStatus.SUCCESS
    assert all(result.countries[country].article_count == 50 for country in CountryCode)
    assert all(len(result.countries[country].top_keywords) == 5 for country in CountryCode)
    assert (site_dir / "latest.json").exists()


def test_live_keyword_batch_does_not_publish_partial_three_country_data(
    tmp_path: Path,
) -> None:
    end = datetime(2026, 8, 8, 0, tzinfo=UTC)
    sources = [
        RssSource(
            source_id=f"{country.value}-{index}",
            country=country,
            publisher=f"{country.value} Publisher {index}",
            feed_url=f"https://example.com/{country.value}/{index}.xml",
            include_summary=False,
        )
        for country in (CountryCode.US, CountryCode.JP)
        for index in range(5)
    ]
    payloads = {
        source.feed_url: _feed(source.country, index % 5, end - timedelta(hours=1))
        for index, source in enumerate(sources)
    }
    site_dir = tmp_path / "site" / "data" / "v2"

    result = run_live_keyword_batch(
        sources,
        [],
        [],
        [],
        payloads.__getitem__,
        lambda _url, _headers: b"{}",
        None,
        None,
        None,
        end - timedelta(hours=24),
        end,
        end.date(),
        tmp_path / "data",
        site_dir,
    )

    assert result.status is IssueStatus.PARTIAL_SUCCESS
    assert not (site_dir / "latest.json").exists()
    assert (tmp_path / "data" / "runtime" / "admin" / "selected-articles.json").exists()


def test_live_keyword_batch_does_not_publish_when_one_country_has_forty_nine_articles(
    tmp_path: Path,
) -> None:
    end = datetime(2026, 8, 9, 0, tzinfo=UTC)
    sources = [
        RssSource(
            source_id=f"{country.value}-{index}",
            country=country,
            publisher=f"{country.value} Publisher {index}",
            feed_url=f"https://example.com/{country.value}/{index}.xml",
            include_summary=False,
        )
        for country in CountryCode
        for index in range(7)
    ]
    payloads = {
        source.feed_url: _feed(
            source.country,
            index % 7,
            end - timedelta(hours=1),
            count=8 if source.country is not CountryCode.KR else 7,
        )
        for index, source in enumerate(sources)
    }
    site_dir = tmp_path / "site" / "data" / "v2"

    result = run_live_keyword_batch(
        sources,
        [],
        [],
        [],
        payloads.__getitem__,
        lambda _url, _headers: b"{}",
        None,
        None,
        None,
        end - timedelta(hours=24),
        end,
        end.date(),
        tmp_path / "data",
        site_dir,
    )

    assert result.status is IssueStatus.PARTIAL_SUCCESS
    assert result.countries[CountryCode.KR].article_count == 49
    assert not (site_dir / "latest.json").exists()
