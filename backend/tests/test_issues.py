from datetime import UTC, datetime, timedelta

import pytest

from app.batch.issues import (
    ExtractedIssue,
    ExtractionResult,
    MockIssueExtractor,
    aggregate_top_issues,
    validate_extraction,
)
from app.batch.models import CollectedArticle
from app.schemas.issues import CountryCode, IssueStatus

NOW = datetime(2026, 8, 6, tzinfo=UTC)


def make_article(
    index: int,
    country: CountryCode = CountryCode.KR,
    title: str = "한국은행 기준금리 동결",
    publisher: str | None = None,
) -> CollectedArticle:
    return CollectedArticle(
        article_id=f"{country.value.lower()}-{index:03d}",
        country=country,
        title=title,
        summary=f"{title} 관련 상세 요약",
        url=f"https://example.com/{country.value.lower()}/{index}",
        publisher=publisher or f"Publisher {index % 4}",
        published_at=NOW - timedelta(minutes=index),
    )


def test_mock_extractor_is_deterministic_and_grounded() -> None:
    articles = [make_article(1), make_article(2)]
    extractor = MockIssueExtractor(
        {article.article_id: ("기준금리 동결", "기준금리 동결") for article in articles}
    )

    first = extractor.extract(CountryCode.KR, articles)
    second = extractor.extract(CountryCode.KR, articles)

    assert first == second
    assert validate_extraction(first, articles) == first


def test_grounding_rejects_unknown_article_and_evidence() -> None:
    articles = [make_article(1)]
    unknown_id = ExtractionResult(
        country=CountryCode.KR,
        issues=(
            ExtractedIssue(
                issue_label="금리",
                display_label_ko="금리",
                article_ids=("kr-999",),
                evidence_expressions=("금리",),
            ),
        ),
        processed_article_ids=("kr-001",),
        model="mock",
        prompt_version="v1",
    )
    with pytest.raises(ValueError, match="article ID"):
        validate_extraction(unknown_id, articles)

    hallucination = unknown_id.model_copy(
        update={
            "issues": (
                unknown_id.issues[0].model_copy(
                    update={"article_ids": ("kr-001",), "evidence_expressions": ("없는 표현",)}
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="evidence"):
        validate_extraction(hallucination, articles)


def test_top_five_merges_similar_labels_and_uses_deterministic_code_ranking() -> None:
    articles = [make_article(index) for index in range(30)]
    secondary_labels = ("원화 환율", "수출 증가", "주택 가격", "고용 개선", "유가 상승")
    labels = {
        article.article_id: (
            "기준금리 동결" if index < 8 else secondary_labels[index % 5],
            "기준금리 동결" if index < 8 else secondary_labels[index % 5],
        )
        for index, article in enumerate(articles)
    }
    extraction = MockIssueExtractor(labels).extract(CountryCode.KR, articles)

    first = aggregate_top_issues(CountryCode.KR, articles, extraction)
    second = aggregate_top_issues(CountryCode.KR, articles, extraction)

    assert first == second
    assert first.status == IssueStatus.SUCCESS
    assert len(first.top_issues) == 5
    assert first.top_issues[0].issue_label == "기준금리 동결"
    assert first.top_issues[0].article_count == 8
    assert [issue.rank for issue in first.top_issues] == [1, 2, 3, 4, 5]


def test_country_mixing_is_rejected() -> None:
    articles = [make_article(1), make_article(2, CountryCode.US, "Federal Reserve decision")]
    extraction = MockIssueExtractor().extract(CountryCode.KR, articles)

    with pytest.raises(ValueError, match="extraction country"):
        validate_extraction(extraction, articles)
