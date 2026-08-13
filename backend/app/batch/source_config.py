from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.batch.collectors.gdelt import GdeltSource
from app.batch.collectors.naver import NaverSource
from app.batch.collectors.newsdata import NewsDataSource
from app.batch.collectors.rss import RssSource
from app.schemas.issues import CountryCode


class SourceEntry(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(min_length=1, max_length=100)
    type: str
    publisher: str = Field(min_length=1, max_length=200)
    provider: str | None = None
    feed_url: str | None = None
    endpoint: str | None = None
    query: str | None = None
    queries: tuple[str, ...] = ()
    query_version: str | None = None
    source_country: str | None = None
    source_language: str | None = None
    allowed_domains: tuple[str, ...] = ()
    excluded_domains: tuple[str, ...] = ()
    blocked_publishers: tuple[str, ...] = ()
    required_title_terms: tuple[str, ...] = ()
    availability_delay_hours: int = Field(default=0, ge=0, le=48)
    max_pages_per_collection: int = Field(default=20, ge=1, le=40)
    max_pages_per_query: int = Field(default=1, ge=1, le=10)
    terms_review_due_at: date | None = None
    enabled: bool = False
    terms_status: str
    allowed_fields: tuple[str, ...]
    source_role: str = "primary"

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"rss", "atom", "api"}:
            raise ValueError("unsupported source type")
        return value

    @field_validator("source_role")
    @classmethod
    def validate_source_role(cls, value: str) -> str:
        if value not in {"primary", "supplementary"}:
            raise ValueError("unsupported source role")
        return value


class SourceRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sources: dict[CountryCode, tuple[SourceEntry, ...]]


def load_rss_sources(source: Path | SourceRegistry) -> list[RssSource]:
    registry = _resolve_registry(source)

    result: list[RssSource] = []
    seen_ids: set[str] = set()
    for country, entries in registry.sources.items():
        for entry in entries:
            _ensure_unique_source_id(entry.id, seen_ids)
            if not entry.enabled or entry.type == "api":
                continue
            if not entry.terms_status.startswith("approved") or entry.feed_url is None:
                raise ValueError(f"Enabled source is not approved: {entry.id}")
            result.append(
                RssSource(
                    source_id=entry.id,
                    country=country,
                    publisher=entry.publisher,
                    feed_url=entry.feed_url,
                    include_summary="summary" in entry.allowed_fields,
                    ranking_weight=0.5 if entry.source_role == "supplementary" else 1.0,
                )
            )
    return result


def load_gdelt_sources(source: Path | SourceRegistry) -> list[GdeltSource]:
    registry = _resolve_registry(source)
    result: list[GdeltSource] = []
    seen_ids: set[str] = set()
    for country, entries in registry.sources.items():
        for entry in entries:
            _ensure_unique_source_id(entry.id, seen_ids)
            if not entry.enabled or entry.type != "api" or entry.provider != "gdelt":
                continue
            required = (
                entry.endpoint,
                entry.query,
                entry.query_version,
                entry.source_country,
                entry.source_language,
            )
            if not entry.terms_status.startswith("approved") or not all(required):
                raise ValueError(f"Enabled GDELT source is incomplete: {entry.id}")
            result.append(
                GdeltSource(
                    source_id=entry.id,
                    country=country,
                    endpoint=entry.endpoint or "",
                    query=entry.query or "",
                    query_version=entry.query_version or "",
                    source_country=entry.source_country or "",
                    source_language=entry.source_language or "",
                    allowed_domains=tuple(
                        domain.lower().removeprefix("www.") for domain in entry.allowed_domains
                    ),
                )
            )
    return result


def load_naver_sources(source: Path | SourceRegistry) -> list[NaverSource]:
    registry = _resolve_registry(source)
    result: list[NaverSource] = []
    seen_ids: set[str] = set()
    for country, entries in registry.sources.items():
        for entry in entries:
            _ensure_unique_source_id(entry.id, seen_ids)
            if not entry.enabled or entry.type != "api" or entry.provider != "naver":
                continue
            if country is not CountryCode.KR:
                raise ValueError("NAVER news source must belong to KR")
            required = (
                entry.endpoint,
                entry.query_version,
                entry.queries,
                entry.terms_review_due_at,
            )
            if (
                not entry.terms_status.startswith("approved")
                or not all(required)
                or not entry.allowed_domains
            ):
                raise ValueError(f"Enabled NAVER source is incomplete: {entry.id}")
            result.append(
                NaverSource(
                    source_id=entry.id,
                    endpoint=entry.endpoint or "",
                    queries=entry.queries,
                    query_version=entry.query_version or "",
                    allowed_domains=tuple(
                        domain.lower().removeprefix("www.") for domain in entry.allowed_domains
                    ),
                    free_policy_review_due_at=entry.terms_review_due_at or date.min,
                    max_pages_per_query=entry.max_pages_per_query,
                )
            )
    return result


def load_newsdata_sources(source: Path | SourceRegistry) -> list[NewsDataSource]:
    registry = _resolve_registry(source)
    result: list[NewsDataSource] = []
    seen_ids: set[str] = set()
    for country, entries in registry.sources.items():
        for entry in entries:
            _ensure_unique_source_id(entry.id, seen_ids)
            if not entry.enabled or entry.type != "api" or entry.provider != "newsdata":
                continue
            if country not in {CountryCode.US, CountryCode.JP}:
                raise ValueError("NewsData supplement must belong to US or JP")
            required = (
                entry.endpoint,
                entry.query_version,
                entry.source_country,
                entry.source_language,
                entry.query,
                entry.terms_review_due_at,
            )
            if not entry.terms_status.startswith("approved") or not all(required):
                raise ValueError(f"Enabled NewsData source is incomplete: {entry.id}")
            result.append(
                NewsDataSource(
                    source_id=entry.id,
                    country=country,
                    endpoint=entry.endpoint or "",
                    api_country=entry.source_country or "",
                    language=entry.source_language or "",
                    category=entry.query or "",
                    query_version=entry.query_version or "",
                    free_policy_review_due_at=entry.terms_review_due_at or date.min,
                    blocked_publishers=entry.blocked_publishers,
                    required_title_terms=entry.required_title_terms,
                    excluded_domains=tuple(
                        domain.lower().removeprefix("www.")
                        for domain in entry.excluded_domains
                    ),
                    availability_delay_hours=entry.availability_delay_hours,
                    max_pages_per_collection=entry.max_pages_per_collection,
                )
            )
    return result


def load_source_registry(path: Path) -> SourceRegistry:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        return SourceRegistry.model_validate(raw)
    except (OSError, ValidationError, ValueError, yaml.YAMLError) as error:
        raise ValueError(f"Invalid source configuration: {path.name}") from error


def _resolve_registry(source: Path | SourceRegistry) -> SourceRegistry:
    return load_source_registry(source) if isinstance(source, Path) else source


def _ensure_unique_source_id(source_id: str, seen_ids: set[str]) -> None:
    if source_id in seen_ids:
        raise ValueError(f"Duplicate source ID: {source_id}")
    seen_ids.add(source_id)
