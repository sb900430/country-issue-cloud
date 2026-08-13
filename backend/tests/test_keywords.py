from datetime import UTC, datetime, timedelta

import pytest

from app.batch.keywords import (
    CandidateSynonymResolver,
    KeywordCandidate,
    KeywordRanker,
    LanguageKeywordExtractor,
    SynonymGroup,
)
from app.batch.models import CollectedArticle
from app.schemas.issues import CountryCode


def _article(
    article_id: str,
    country: CountryCode,
    title: str,
    publisher: str = "example.com",
    offset: int = 0,
) -> CollectedArticle:
    return CollectedArticle(
        article_id=article_id,
        country=country,
        title=title,
        url=f"https://example.com/{article_id}",
        publisher=publisher,
        published_at=datetime(2026, 8, 8, tzinfo=UTC) + timedelta(minutes=offset),
    )


@pytest.mark.parametrize(
    ("country", "title", "expected", "evidence"),
    [
        (CountryCode.US, "Interest rate outlook changes 001", "interest rate", "interest rate"),
        (CountryCode.JP, "円相場の変動性が上昇 001", "円相場変動性", "円相場の変動性"),
        (CountryCode.KR, "기준금리 전망 변화 001", "기준금리", "기준금리"),
    ],
)
def test_language_extractors_keep_compound_nouns_and_remove_reporting_tails(
    country: CountryCode, title: str, expected: str, evidence: str
) -> None:
    candidates = LanguageKeywordExtractor().extract(_article("article", country, title))

    assert candidates == (KeywordCandidate(label=expected, evidence_expression=evidence),)


@pytest.mark.parametrize(
    ("country", "title"),
    [
        (CountryCode.US, "News markets today 001"),
        (CountryCode.JP, "経済ニュース市場速報 001"),
        (CountryCode.KR, "경제 뉴스 시장 영향 001"),
    ],
)
def test_general_terms_do_not_become_candidates(country: CountryCode, title: str) -> None:
    candidates = LanguageKeywordExtractor().extract(_article("article", country, title))

    assert candidates == ()


@pytest.mark.parametrize(
    ("country", "title", "blocked"),
    [
        (
            CountryCode.US,
            "Quarterly earnings results and stock price moving average",
            {"earning result", "stock price", "moving average"},
        ),
        (CountryCode.JP, "2026年8月に新商品を発売", {"2026年", "8月", "発売", "年8月"}),
        (
            CountryCode.KR,
            "[특징주] 400억원 규모 신상품 출시 호실적",
            {"특징주", "억원", "원규모", "출시", "호실적"},
        ),
    ],
)
def test_template_dates_units_and_section_labels_are_not_candidates(
    country: CountryCode, title: str, blocked: set[str]
) -> None:
    labels = {
        candidate.label
        for candidate in LanguageKeywordExtractor().extract(_article("article", country, title))
    }

    assert labels.isdisjoint(blocked)


def test_english_normalization_keeps_s_ending_singular_words() -> None:
    candidates = LanguageKeywordExtractor().extract(
        _article("article", CountryCode.US, "Analysis report exports 001")
    )

    assert candidates == (
        KeywordCandidate(label="analysis", evidence_expression="analysis"),
        KeywordCandidate(label="export", evidence_expression="exports"),
    )


def test_long_japanese_title_produces_only_short_evidence_backed_concepts() -> None:
    title = "半導体投資" * 30

    candidates = LanguageKeywordExtractor().extract(_article("article", CountryCode.JP, title))

    assert candidates
    assert all(len(candidate.label) <= 30 for candidate in candidates)
    assert all(candidate.evidence_expression in title for candidate in candidates)


def test_single_character_japanese_fragment_does_not_hide_valid_concept() -> None:
    candidates = LanguageKeywordExtractor().extract(
        _article("article", CountryCode.JP, "米が利上げを検討")
    )

    assert candidates == (KeywordCandidate(label="利上げ", evidence_expression="利上げ"),)


def test_synonym_resolver_only_uses_labels_present_in_candidates() -> None:
    resolver = CandidateSynonymResolver(
        (SynonymGroup(aliases=("interest rate", "policy rate", "benchmark rate")),)
    )

    assert resolver.group_key("policy rate") == resolver.group_key("benchmark rate")
    assert resolver.display_label({"policy rate", "benchmark rate"}) == "policy rate"


def test_ranker_rejects_small_samples_and_country_mixing() -> None:
    articles = [
        _article(str(index), CountryCode.US, "semiconductor investment expands")
        for index in range(49)
    ]
    with pytest.raises(ValueError, match="at least 50"):
        KeywordRanker().analyze(CountryCode.US, articles)

    articles.append(_article("mixed", CountryCode.JP, "半導体投資が拡大"))
    with pytest.raises(ValueError, match="cannot mix"):
        KeywordRanker().analyze(CountryCode.US, articles)


def test_ranker_merges_only_configured_candidate_synonyms() -> None:
    topics = (
        "interest rate",
        "benchmark rate",
        "semiconductor investment",
        "dollar volatility",
        "climate policy",
        "housing demand",
    )
    articles = [
        _article(
            f"article-{index:03d}",
            CountryCode.US,
            f"{topics[index % len(topics)]} {index:03d}",
            publisher=f"publisher-{index % 5}",
            offset=index,
        )
        for index in range(120)
    ]
    resolver = CandidateSynonymResolver(
        (SynonymGroup(aliases=("interest rate", "benchmark rate")),)
    )

    result = KeywordRanker(resolver=resolver).analyze(CountryCode.US, articles)

    assert result.top_keywords[0].label == "interest rate"
    assert result.top_keywords[0].document_frequency == 40
    assert "benchmark rate" not in {keyword.label for keyword in result.top_keywords}


def test_ranker_excludes_rare_and_single_publisher_words() -> None:
    topics = ("semiconductor", "inflation", "currency", "export", "housing")
    articles = []
    for index in range(120):
        suffix = " report monopoly" if index < 10 else " report scarcity" if index < 12 else ""
        articles.append(
            _article(
                f"article-{index:03d}",
                CountryCode.US,
                f"{topics[index % len(topics)]}{suffix} {index:03d}",
                publisher=(
                    "publisher-0" if index < 10 else f"publisher-{(index + index // 5) % 5}"
                ),
                offset=index,
            )
        )

    result = KeywordRanker().analyze(CountryCode.US, articles)

    labels = {keyword.label for keyword in result.top_keywords}
    assert labels == set(topics)
    assert "monopoly" not in labels
    assert "scarcity" not in labels
    assert all(keyword.document_frequency >= 6 for keyword in result.top_keywords)
    assert all(keyword.publisher_count >= 2 for keyword in result.top_keywords)


def test_ranker_does_not_publish_two_keywords_backed_by_the_same_articles() -> None:
    topics = (
        "supply chain resilience",
        "semiconductor",
        "inflation",
        "currency",
        "export",
        "housing",
    )
    articles = [
        _article(
            f"article-{index:03d}",
            CountryCode.US,
            f"{topics[index % len(topics)]} {index:03d}",
            publisher=f"publisher-{index % 5}",
            offset=index,
        )
        for index in range(120)
    ]

    result = KeywordRanker().analyze(CountryCode.US, articles)

    labels = {keyword.label for keyword in result.top_keywords}
    assert not {"supply chain", "chain resilience"} <= labels
    assert len(labels) == 5
