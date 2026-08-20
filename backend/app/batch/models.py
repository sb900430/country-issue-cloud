from datetime import datetime
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.schemas.issues import CountryCode


class CollectorKind(StrEnum):
    FIXTURE = "fixture"
    LIVE = "live"


class CollectedArticle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str = Field(min_length=1, max_length=128)
    country: CountryCode
    title: str = Field(min_length=1, max_length=500)
    summary: str | None = Field(default=None, max_length=2_000)
    url: str = Field(min_length=1, max_length=2_048)
    publisher: str = Field(min_length=1, max_length=200)
    published_at: AwareDatetime
    ranking_weight: float = Field(default=1.0, gt=0, le=1)
    story_cluster_id: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("url")
    @classmethod
    def validate_https_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("URL must use HTTPS")
        return value


class CountryCollectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    country: CountryCode
    articles: tuple[CollectedArticle, ...] = ()
    errors: tuple[str, ...] = ()
    source_article_counts: dict[str, int] = Field(default_factory=dict)
    source_filter_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    source_rejected_domain_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    source_publisher_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    raw_article_count: int = Field(default=0, ge=0)
    deduplicated_article_count: int = Field(default=0, ge=0)
    story_cluster_count: int = Field(default=0, ge=0)
    diversity_weighted_article_count: float = Field(default=0, ge=0)
    used_fixture_fallback: bool = False
    collected_at: datetime
