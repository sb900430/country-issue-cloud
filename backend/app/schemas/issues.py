from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator


class CountryCode(StrEnum):
    US = "US"
    JP = "JP"
    KR = "KR"


class IssueStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RepresentativeArticle(StrictSchema):
    title: Annotated[str, Field(min_length=1, max_length=500)]
    publisher: Annotated[str, Field(min_length=1, max_length=200)]
    published_at: AwareDatetime
    url: HttpUrl


class TopIssue(StrictSchema):
    rank: Annotated[int, Field(ge=1, le=5)]
    issue_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,99}$")]
    issue_label: Annotated[str, Field(min_length=1, max_length=120)]
    display_label_ko: Annotated[str, Field(min_length=1, max_length=120)]
    article_count: Annotated[int, Field(ge=1)]
    publisher_count: Annotated[int, Field(ge=1)]
    article_ratio: Annotated[float, Field(gt=0, le=1)]
    representative_articles: Annotated[list[RepresentativeArticle], Field(min_length=1)]


class CountryIssueResult(StrictSchema):
    status: IssueStatus
    article_count: Annotated[int, Field(ge=0)]
    extraction_success_rate: Annotated[float, Field(ge=0, le=1)]
    top_issues: Annotated[list[TopIssue], Field(max_length=5)]
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_issue_totals(self) -> "CountryIssueResult":
        ranks = [issue.rank for issue in self.top_issues]
        if len(ranks) != len(set(ranks)):
            raise ValueError("top_issues ranks must be unique")
        if any(issue.article_count > self.article_count for issue in self.top_issues):
            raise ValueError("top issue article_count cannot exceed country article_count")
        return self


class IssueResult(StrictSchema):
    schema_version: Literal["1.0"]
    date: date
    generated_at: AwareDatetime
    status: IssueStatus
    countries: dict[CountryCode, CountryIssueResult]

    @model_validator(mode="after")
    def validate_country_set(self) -> "IssueResult":
        if set(self.countries) != set(CountryCode):
            raise ValueError("countries must contain exactly US, JP, and KR")
        return self
