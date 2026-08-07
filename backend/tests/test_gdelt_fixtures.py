from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.batch.collectors.gdelt import GdeltCollector, GdeltSource
from app.batch.deduplication import select_diverse_articles
from app.schemas.issues import CountryCode

WINDOW_END = datetime(2026, 8, 7, 0, 0, tzinfo=UTC)
WINDOW_START = WINDOW_END - timedelta(hours=24)
PROJECT_ROOT = Path(__file__).parents[2]
DOMAINS = {
    CountryCode.US: ("wsj.com", "bloomberg.com", "cnbc.com", "marketwatch.com", "reuters.com"),
    CountryCode.JP: ("nikkei.com", "toyokeizai.net", "diamond.jp", "jiji.com", "newswitch.jp"),
    CountryCode.KR: ("hankyung.com", "mk.co.kr", "sedaily.com", "edaily.co.kr", "mt.co.kr"),
}
SOURCE_COUNTRIES = {
    CountryCode.US: "UnitedStates",
    CountryCode.JP: "Japan",
    CountryCode.KR: "SouthKorea",
}
SOURCE_LANGUAGES = {
    CountryCode.US: "English",
    CountryCode.JP: "Japanese",
    CountryCode.KR: "Korean",
}


def test_country_gdelt_fixtures_keep_at_least_one_hundred_diverse_articles() -> None:
    for country in CountryCode:
        fixture = PROJECT_ROOT / "sample-data" / "evaluation" / country.value / "gdelt.json"
        source = GdeltSource(
            source_id=f"gdelt-{country.value.lower()}",
            country=country,
            endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
            query=" OR ".join(f"domain:{domain}" for domain in DOMAINS[country]),
            query_version="fixture.v1",
            source_country=SOURCE_COUNTRIES[country],
            source_language=SOURCE_LANGUAGES[country],
            allowed_domains=DOMAINS[country],
        )
        articles = GdeltCollector(source, lambda _, path=fixture: path.read_bytes()).collect(
            WINDOW_START, WINDOW_END, 250
        )

        selected = select_diverse_articles(articles, 250)

        assert len(articles) == 120
        assert len(selected) == 120
        assert len({article.publisher for article in selected}) == 5
