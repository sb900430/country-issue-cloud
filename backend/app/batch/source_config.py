from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.batch.collectors.rss import RssSource
from app.schemas.issues import CountryCode


class SourceEntry(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(min_length=1, max_length=100)
    type: str
    publisher: str = Field(min_length=1, max_length=200)
    feed_url: str | None = None
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


def load_rss_sources(path: Path) -> list[RssSource]:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        registry = SourceRegistry.model_validate(raw)
    except (OSError, ValidationError, ValueError, yaml.YAMLError) as error:
        raise ValueError(f"Invalid source configuration: {path.name}") from error

    result: list[RssSource] = []
    seen_ids: set[str] = set()
    for country, entries in registry.sources.items():
        for entry in entries:
            if entry.id in seen_ids:
                raise ValueError(f"Duplicate source ID: {entry.id}")
            seen_ids.add(entry.id)
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
