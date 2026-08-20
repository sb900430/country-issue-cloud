from datetime import UTC, date, datetime

from pydantic import HttpUrl, TypeAdapter

from app.batch.keyword_translation import GlossaryKeywordTranslator, KeywordTranslator
from app.batch.keywords import KeywordRanker
from app.batch.models import CountryCollectionResult
from app.schemas.issues import CountryCode, IssueStatus
from app.schemas.keywords import CountryKeywordResult, KeywordResult, RelatedArticle, TopKeyword


def build_keyword_result(
    target_date: date,
    collections: dict[CountryCode, CountryCollectionResult],
    ranker: KeywordRanker | None = None,
    translator: KeywordTranslator | None = None,
    generated_at: datetime | None = None,
) -> KeywordResult:
    resolved_ranker = ranker or KeywordRanker()
    resolved_translator = translator or GlossaryKeywordTranslator.load()
    countries: dict[CountryCode, CountryKeywordResult] = {}
    for country in CountryCode:
        collection = collections.get(country)
        if collection is None:
            countries[country] = _failed_country("collection_unavailable")
            continue
        articles = list(collection.articles)
        try:
            analysis = resolved_ranker.analyze(country, articles)
        except ValueError as error:
            countries[country] = CountryKeywordResult(
                status=IssueStatus.FAILED,
                article_count=len(articles),
                top_keywords=[],
                warnings=[_analysis_warning(error), *collection.errors],
            )
            continue
        indexed = {article.article_id: article for article in articles}
        countries[country] = CountryKeywordResult(
            status=IssueStatus.SUCCESS,
            article_count=analysis.article_count,
            top_keywords=[
                TopKeyword(
                    rank=keyword.rank,
                    keyword_id=keyword.keyword_id,
                    label=keyword.label,
                    label_ko=resolved_translator.translate_to_korean(country, keyword.label),
                    document_frequency=keyword.document_frequency,
                    publisher_count=keyword.publisher_count,
                    article_ratio=keyword.article_ratio,
                    evidence_expressions=list(keyword.evidence_expressions),
                    related_articles=[
                        RelatedArticle(
                            article_id=article_id,
                            title=indexed[article_id].title,
                            publisher=indexed[article_id].publisher,
                            published_at=indexed[article_id].published_at,
                            url=TypeAdapter(HttpUrl).validate_python(indexed[article_id].url),
                        )
                        for article_id in keyword.related_article_ids
                    ],
                )
                for keyword in analysis.top_keywords
            ],
            warnings=list(collection.errors),
        )
    successful = sum(value.status is IssueStatus.SUCCESS for value in countries.values())
    status = (
        IssueStatus.SUCCESS
        if successful == 3
        else IssueStatus.PARTIAL_SUCCESS
        if successful >= 1
        else IssueStatus.FAILED
    )
    return KeywordResult(
        schema_version="2.0",
        date=target_date,
        generated_at=generated_at or datetime.now(UTC),
        status=status,
        countries=countries,
    )


def _failed_country(warning: str) -> CountryKeywordResult:
    return CountryKeywordResult(
        status=IssueStatus.FAILED,
        article_count=0,
        top_keywords=[],
        warnings=[warning],
    )


def _analysis_warning(error: ValueError) -> str:
    message = str(error)
    if "at least 50 articles" in message:
        reason = "insufficient_articles"
    elif "at least 30 stories" in message:
        reason = "insufficient_stories"
    elif "fewer than three candidates" in message:
        reason = "insufficient_quality_candidates"
    elif "cannot mix countries" in message:
        reason = "invalid_country_mix"
    else:
        reason = type(error).__name__
    return f"keyword_analysis_failed:{reason}"
