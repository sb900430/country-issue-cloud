from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.batch.collectors.rss import RssSource
from app.batch.live import run_live_batch
from app.schemas.issues import CountryCode, IssueStatus


def _feed(
    country: CountryCode, published_at: datetime, publisher_index: int, count: int = 3
) -> bytes:
    labels = (
        "inflation",
        "employment",
        "exports",
        "housing",
        "technology",
        "energy",
        "healthcare",
        "education",
        "transport",
        "agriculture",
        "currency",
        "manufacturing",
        "tourism",
        "budget",
        "startups",
    )
    items = "".join(
        f"""
        <item>
          <title>{label} {country.value} publisher {publisher_index}</title>
          <link>https://example.com/{country.value.lower()}/{publisher_index}/{index}</link>
          <pubDate>{published_at.strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
        </item>
        """
        for index, label in enumerate(
            labels[publisher_index * count : (publisher_index + 1) * count]
        )
    )
    return f"<rss><channel>{items}</channel></rss>".encode()


def test_live_batch_collects_three_countries_and_publishes_json(tmp_path: Path) -> None:
    end = datetime(2026, 8, 6, 12, tzinfo=UTC)
    sources = [
        RssSource(
            source_id=f"{country.value.lower()}-source-{publisher_index}",
            country=country,
            publisher=f"{country.value} Publisher {publisher_index}",
            feed_url=(
                f"https://example.com/{country.value.lower()}-{publisher_index}.xml"
            ),
            include_summary=False,
        )
        for country in CountryCode
        for publisher_index in range(5)
    ]
    payloads = {
        source.feed_url: _feed(
            source.country,
            end - timedelta(hours=1),
            int(source.source_id.rsplit("-", 1)[1]),
        )
        for source in sources
    }

    result = run_live_batch(
        sources,
        [],
        [],
        payloads.__getitem__,
        lambda _url, _headers: b"{}",
        None,
        None,
        end - timedelta(days=1),
        end,
        end.date(),
        tmp_path / "data",
        tmp_path / "site" / "data" / "v1",
    )

    assert result.status is IssueStatus.SUCCESS
    assert all(result.countries[country].article_count == 15 for country in CountryCode)
    assert (tmp_path / "site" / "data" / "v1" / "latest.json").exists()
