import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from hashlib import sha256
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter

from app.batch.models import CollectedArticle
from app.schemas.issues import (
    CountryCode,
    CountryIssueResult,
    IssueStatus,
    RepresentativeArticle,
    TopIssue,
)


class ExtractedIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issue_label: str = Field(min_length=1, max_length=120)
    display_label_ko: str = Field(min_length=1, max_length=120)
    article_ids: tuple[str, ...] = Field(min_length=1)
    evidence_expressions: tuple[str, ...] = Field(min_length=1)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    country: CountryCode
    issues: tuple[ExtractedIssue, ...]
    processed_article_ids: tuple[str, ...]
    model: str
    prompt_version: str
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0, ge=0)


class IssueExtractor(Protocol):
    def extract(
        self, country: CountryCode, articles: list[CollectedArticle]
    ) -> ExtractionResult: ...


class MockIssueExtractor:
    def __init__(self, labels: dict[str, tuple[str, str]] | None = None) -> None:
        self.labels = labels or {}

    def extract(
        self, country: CountryCode, articles: list[CollectedArticle]
    ) -> ExtractionResult:
        issues = []
        for article in articles:
            label, display_label = self.labels.get(
                article.article_id, (article.title, article.title)
            )
            label = label[:120].strip()
            display_label = display_label[:120].strip()
            issues.append(
                ExtractedIssue(
                    issue_label=label,
                    display_label_ko=display_label,
                    article_ids=(article.article_id,),
                    evidence_expressions=(article.title,),
                )
            )
        return ExtractionResult(
            country=country,
            issues=tuple(issues),
            processed_article_ids=tuple(article.article_id for article in articles),
            model="mock-deterministic-v1",
            prompt_version="issues-v1",
        )


def validate_extraction(
    extraction: ExtractionResult, articles: list[CollectedArticle]
) -> ExtractionResult:
    if any(article.country != extraction.country for article in articles):
        raise ValueError("articles must belong to the extraction country")
    indexed = {article.article_id: article for article in articles}
    if not set(extraction.processed_article_ids).issubset(indexed):
        raise ValueError("processed article ID is not present in the input")
    for issue in extraction.issues:
        if not set(issue.article_ids).issubset(indexed):
            raise ValueError("issue article ID is not present in the input")
        searchable = " ".join(
            f"{indexed[article_id].title} {indexed[article_id].summary or ''}"
            for article_id in issue.article_ids
        ).casefold()
        if any(evidence.casefold() not in searchable for evidence in issue.evidence_expressions):
            raise ValueError("evidence expression is not present in the input")
    return extraction


def aggregate_top_issues(
    country: CountryCode,
    articles: list[CollectedArticle],
    extraction: ExtractionResult,
) -> CountryIssueResult:
    validate_extraction(extraction, articles)
    indexed = {article.article_id: article for article in articles}
    clusters: list[list[ExtractedIssue]] = []
    for issue in extraction.issues:
        cluster = next(
            (
                candidate
                for candidate in clusters
                if _similar(candidate[0].issue_label, issue.issue_label)
            ),
            None,
        )
        if cluster is None:
            clusters.append([issue])
        else:
            cluster.append(issue)

    ranked: list[tuple[float, int, datetime, str, TopIssue]] = []
    for cluster in clusters:
        article_ids = sorted({article_id for issue in cluster for article_id in issue.article_ids})
        cluster_articles = [indexed[article_id] for article_id in article_ids]
        label = _preferred_label(cluster)
        issue_id = _issue_id(country, label)
        publisher_count = len({article.publisher for article in cluster_articles})
        latest = max(article.published_at for article in cluster_articles)
        representative = sorted(
            cluster_articles,
            key=lambda article: (not bool(article.summary), -article.published_at.timestamp()),
        )[:3]
        ranked.append(
            (
                sum(article.ranking_weight for article in cluster_articles),
                publisher_count,
                latest,
                issue_id,
                TopIssue(
                    rank=1,
                    issue_id=issue_id,
                    issue_label=label,
                    display_label_ko=_preferred_display_label(cluster),
                    article_count=len(cluster_articles),
                    publisher_count=publisher_count,
                    article_ratio=len(cluster_articles) / len(articles),
                    representative_articles=[
                        RepresentativeArticle(
                            title=article.title,
                            publisher=article.publisher,
                            published_at=article.published_at,
                            url=TypeAdapter(HttpUrl).validate_python(article.url),
                        )
                        for article in representative
                    ],
                ),
            )
        )
    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2].timestamp(), item[3]))
    top_issues = [
        item[4].model_copy(update={"rank": rank})
        for rank, item in enumerate(ranked[:5], 1)
    ]
    success_rate = (
        len(set(extraction.processed_article_ids)) / len(articles) if articles else 0.0
    )
    if len(articles) >= 15 and success_rate >= 0.8 and len(top_issues) >= 3:
        status = IssueStatus.SUCCESS
    elif len(articles) >= 5 and success_rate >= 0.7 and top_issues:
        status = IssueStatus.PARTIAL_SUCCESS
    else:
        status = IssueStatus.FAILED
    return CountryIssueResult(
        status=status,
        article_count=len(articles),
        extraction_success_rate=success_rate,
        top_issues=top_issues,
        warnings=[] if status != IssueStatus.FAILED else ["publication_threshold_not_met"],
    )


def _normalize_label(label: str) -> str:
    text = unicodedata.normalize("NFKC", label).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def _similar(left: str, right: str) -> bool:
    normalized_left = _normalize_label(left)
    normalized_right = _normalize_label(right)
    return normalized_left == normalized_right or SequenceMatcher(
        None, normalized_left, normalized_right
    ).ratio() >= 0.88


def _preferred_label(issues: list[ExtractedIssue]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for issue in issues:
        counts[issue.issue_label] += len(set(issue.article_ids))
    return min(counts, key=lambda label: (-counts[label], len(label), label))


def _preferred_display_label(issues: list[ExtractedIssue]) -> str:
    preferred = _preferred_label(issues)
    return next(issue.display_label_ko for issue in issues if issue.issue_label == preferred)


def _issue_id(country: CountryCode, label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", label).lower()).strip("-")
    digest = sha256(f"{country}:{_normalize_label(label)}".encode()).hexdigest()[:10]
    if slug:
        return f"{country.value.lower()}-{slug[:40]}-{digest}"
    return f"{country.value.lower()}-{digest}"
