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


def test_general_terms_do_not_become_candidates() -> None:
    candidates = LanguageKeywordExtractor().extract(
        _article("article", CountryCode.KR, "경제 뉴스 시장 영향 001")
    )

    assert candidates == ()


def test_long_japanese_title_is_bounded_without_losing_source_evidence() -> None:
    title = "半導体投資" * 30

    candidate = LanguageKeywordExtractor().extract(_article("article", CountryCode.JP, title))[0]

    assert len(candidate.label) == 80
    assert len(candidate.evidence_expression) == 120
    assert candidate.evidence_expression in title


def test_single_character_japanese_fragment_is_skipped() -> None:
    candidates = LanguageKeywordExtractor().extract(
        _article("article", CountryCode.JP, "米が利上げを検討")
    )

    assert candidates == ()


def test_synonym_resolver_only_uses_labels_present_in_candidates() -> None:
    resolver = CandidateSynonymResolver(
        (SynonymGroup(aliases=("interest rate", "policy rate", "benchmark rate")),)
    )

    assert resolver.group_key("policy rate") == resolver.group_key("benchmark rate")
    assert resolver.display_label({"policy rate", "benchmark rate"}) == "policy rate"


def test_ranker_rejects_small_samples_and_country_mixing() -> None:
    articles = [
        _article(str(index), CountryCode.US, "semiconductor investment expands")
        for index in range(99)
    ]
    with pytest.raises(ValueError, match="at least 100"):
        KeywordRanker().analyze(CountryCode.US, articles)

    articles.append(_article("mixed", CountryCode.JP, "半導体投資が拡大"))
    with pytest.raises(ValueError, match="cannot mix"):
        KeywordRanker().analyze(CountryCode.US, articles)


def test_ranker_merges_only_configured_candidate_synonyms() -> None:
    topics = (
        "interest rate",
        "policy rate",
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
    resolver = CandidateSynonymResolver((SynonymGroup(aliases=("interest rate", "policy rate")),))

    result = KeywordRanker(resolver=resolver).analyze(CountryCode.US, articles)

    assert result.top_keywords[0].label == "interest rate"
    assert result.top_keywords[0].document_frequency == 40
    assert "policy rate" not in {keyword.label for keyword in result.top_keywords}
