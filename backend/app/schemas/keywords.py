from datetime import date
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, HttpUrl, model_validator

from app.schemas.issues import CountryCode, IssueStatus, StrictSchema


class RelatedArticle(StrictSchema):
    article_id: Annotated[str, Field(min_length=1, max_length=128)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    publisher: Annotated[str, Field(min_length=1, max_length=200)]
    published_at: AwareDatetime
    url: HttpUrl


class TopKeyword(StrictSchema):
    rank: Annotated[int, Field(ge=1, le=5)]
    keyword_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,79}$")]
    label: Annotated[str, Field(min_length=2, max_length=80)]
    document_frequency: Annotated[int, Field(ge=1)]
    publisher_count: Annotated[int, Field(ge=1)]
    article_ratio: Annotated[float, Field(gt=0, le=1)]
    evidence_expressions: Annotated[list[str], Field(min_length=1, max_length=10)]
    related_articles: Annotated[list[RelatedArticle], Field(min_length=1, max_length=20)]


class CountryKeywordResult(StrictSchema):
    status: IssueStatus
    article_count: Annotated[int, Field(ge=0)]
    top_keywords: Annotated[list[TopKeyword], Field(max_length=5)]
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_keyword_totals(self) -> "CountryKeywordResult":
        ranks = [keyword.rank for keyword in self.top_keywords]
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError("top keyword ranks must be contiguous")
        if any(keyword.document_frequency > self.article_count for keyword in self.top_keywords):
            raise ValueError("keyword frequency cannot exceed country article count")
        if self.status is IssueStatus.SUCCESS and not 3 <= len(self.top_keywords) <= 5:
            raise ValueError("successful country must contain three to five keywords")
        return self


class KeywordResult(StrictSchema):
    schema_version: Literal["2.0"]
    date: date
    generated_at: AwareDatetime
    status: IssueStatus
    countries: dict[CountryCode, CountryKeywordResult]

    @model_validator(mode="after")
    def validate_country_set(self) -> "KeywordResult":
        if set(self.countries) != set(CountryCode):
            raise ValueError("countries must contain exactly US, JP, and KR")
        return self
