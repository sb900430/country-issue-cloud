from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from app.batch.collectors.gdelt import GdeltCollector, GdeltSource
from app.batch.keyword_pipeline import build_keyword_result
from app.batch.keyword_publishing import KeywordStaticJsonPublisher
from app.batch.models import CountryCollectionResult
from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.issues import CountryCode
from app.schemas.keywords import KeywordResult

_DOMAINS = {
    CountryCode.US: ("wsj.com", "bloomberg.com", "cnbc.com", "marketwatch.com", "reuters.com"),
    CountryCode.JP: ("nikkei.com", "toyokeizai.net", "diamond.jp", "jiji.com", "newswitch.jp"),
    CountryCode.KR: ("hankyung.com", "mk.co.kr", "sedaily.com", "edaily.co.kr", "mt.co.kr"),
}
_SOURCE_COUNTRIES = {
    CountryCode.US: "UnitedStates",
    CountryCode.JP: "Japan",
    CountryCode.KR: "SouthKorea",
}
_SOURCE_LANGUAGES = {
    CountryCode.US: "English",
    CountryCode.JP: "Japanese",
    CountryCode.KR: "Korean",
}


def publish_keyword_fixture(
    evaluation_dir: Path,
    data_dir: Path,
    site_data_dir: Path,
    target_date: date = date(2026, 8, 7),
) -> KeywordResult:
    window_end = datetime(2026, 8, 7, tzinfo=UTC)
    window_start = window_end - timedelta(hours=24)
    collections: dict[CountryCode, CountryCollectionResult] = {}
    for country in CountryCode:
        fixture = evaluation_dir / country.value / "gdelt.json"

        def fetch_fixture(_url: str, path: Path = fixture) -> bytes:
            return path.read_bytes()

        source = GdeltSource(
            source_id=f"gdelt-{country.value.lower()}-fixture",
            country=country,
            endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
            query=" OR ".join(f"domain:{domain}" for domain in _DOMAINS[country]),
            query_version="fixture.v1",
            source_country=_SOURCE_COUNTRIES[country],
            source_language=_SOURCE_LANGUAGES[country],
            allowed_domains=_DOMAINS[country],
        )
        articles = GdeltCollector(source, fetch_fixture).collect(window_start, window_end, 250)
        collections[country] = CountryCollectionResult(
            country=country,
            articles=tuple(articles),
            collected_at=window_end,
        )
    result = build_keyword_result(target_date, collections, generated_at=window_end)
    repository = JsonKeywordRepository(data_dir)
    repository.save(result)
    KeywordStaticJsonPublisher(repository.published_dir, site_data_dir).publish()
    return result
