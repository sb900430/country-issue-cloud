from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.batch.collectors.gdelt import GdeltCollector, GdeltSource
from app.batch.keywords import KeywordRanker
from app.schemas.issues import CountryCode

WINDOW_END = datetime(2026, 8, 7, tzinfo=UTC)
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
EXPECTED_LABELS = {
    CountryCode.US: {
        "semiconductor",
        "interest rate",
        "dollar volatility",
        "climate",
        "housing",
    },
    CountryCode.JP: {"半導体", "金利", "円相場変動性", "気候", "住宅"},
    CountryCode.KR: {"반도체", "기준금리", "원화변동성", "기후", "주택"},
}


def _fixture_articles(country: CountryCode):
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
    return GdeltCollector(source, lambda _: fixture.read_bytes()).collect(
        WINDOW_START, WINDOW_END, 250
    )


def test_country_fixtures_produce_deterministic_evidence_backed_top_five() -> None:
    ranker = KeywordRanker()
    for country in CountryCode:
        articles = _fixture_articles(country)
        first = ranker.analyze(country, articles)
        second = ranker.analyze(country, list(reversed(articles)))

        assert first == second
        assert first.article_count == 120
        assert {keyword.label for keyword in first.top_keywords} == EXPECTED_LABELS[country]
        assert all(keyword.document_frequency == 24 for keyword in first.top_keywords)
        assert all(keyword.publisher_count == 5 for keyword in first.top_keywords)
        assert all(
            len(keyword.label.split()) <= 2
            if country is CountryCode.US
            else " " not in keyword.label
            for keyword in first.top_keywords
        )
        assert all(len(keyword.related_article_ids) == 20 for keyword in first.top_keywords)
        assert len({keyword.keyword_id for keyword in first.top_keywords}) == 5
        indexed = {article.article_id: article for article in articles}
        assert all(
            set(keyword.related_article_ids).issubset(indexed) for keyword in first.top_keywords
        )
        assert all(
            any(
                evidence.casefold() in indexed[article_id].title.casefold()
                for article_id in keyword.related_article_ids
            )
            for keyword in first.top_keywords
            for evidence in keyword.evidence_expressions
        )
