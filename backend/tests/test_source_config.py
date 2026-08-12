from pathlib import Path

import pytest

from app.batch.source_config import (
    load_gdelt_sources,
    load_naver_sources,
    load_newsdata_sources,
    load_rss_sources,
)
from app.schemas.issues import CountryCode


def test_source_registry_loads_only_approved_enabled_feeds(tmp_path: Path) -> None:
    config = tmp_path / "sources.yml"
    config.write_text(
        """
sources:
  US:
    - id: active
      type: rss
      publisher: Publisher
      feed_url: https://example.com/feed.xml
      enabled: true
      terms_status: approved
      allowed_fields: [title, url, publisher, published_at]
      source_role: supplementary
    - id: disabled-api
      type: api
      publisher: API Publisher
      enabled: false
      terms_status: registration_required
      allowed_fields: [title, url, publisher, published_at]
  JP: []
  KR: []
""".strip(),
        encoding="utf-8",
    )

    sources = load_rss_sources(config)

    assert len(sources) == 1
    assert sources[0].source_id == "active"
    assert sources[0].country is CountryCode.US
    assert sources[0].include_summary is False
    assert sources[0].ranking_weight == 0.5


def test_source_registry_rejects_unapproved_enabled_feed(tmp_path: Path) -> None:
    config = tmp_path / "sources.yml"
    config.write_text(
        """
sources:
  US:
    - id: unsafe
      type: rss
      publisher: Publisher
      feed_url: https://example.com/feed.xml
      enabled: true
      terms_status: registration_required
      allowed_fields: [title, url, publisher, published_at]
  JP: []
  KR: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not approved"):
        load_rss_sources(config)


def test_project_source_registry_has_feeds_for_every_country() -> None:
    project_root = Path(__file__).parents[2]

    sources = load_rss_sources(project_root / "config" / "sources.example.yml")

    assert {source.country for source in sources} == set(CountryCode)
    assert all(source.feed_url.startswith("https://") for source in sources)
    source_ids = {source.source_id for source in sources}
    assert {
        "census_economic_indicators",
        "bea_news_releases",
        "mof_japan_updates",
        "statistics_japan_updates",
        "jpx_market_news",
        "jpx_news_releases",
        "fsa_japan_updates",
    } <= source_ids


def test_project_source_registry_keeps_rate_limited_gdelt_disabled() -> None:
    project_root = Path(__file__).parents[2]

    sources = load_gdelt_sources(project_root / "config" / "sources.example.yml")

    assert sources == []


def test_project_source_registry_has_naver_supplement_for_korea() -> None:
    project_root = Path(__file__).parents[2]

    sources = load_naver_sources(project_root / "config" / "sources.example.yml")

    assert len(sources) == 1
    assert sources[0].queries[:2] == ("경제", "금융")
    assert {
        "hankyung.com",
        "newsis.com",
        "yna.co.kr",
        "econovill.com",
        "metroseoul.co.kr",
        "hansbiz.co.kr",
        "g-enews.com",
        "ekn.kr",
    } <= set(sources[0].allowed_domains)
    assert {
        "dailian.co.kr",
        "munhwa.com",
        "mbn.mk.co.kr",
        "yonhapnewstv.co.kr",
    } <= set(sources[0].allowed_domains)
    assert sources[0].query_version == "2026-08-12.v5"
    assert sources[0].max_pages_per_query == 2


def test_project_source_registry_has_newsdata_supplements_for_us_and_japan() -> None:
    project_root = Path(__file__).parents[2]

    sources = load_newsdata_sources(project_root / "config" / "sources.example.yml")

    assert {source.country for source in sources} == {CountryCode.US, CountryCode.JP}
    assert {source.api_country for source in sources} == {"us", "jp"}
    assert all(source.category == "business" for source in sources)
    us = next(source for source in sources if source.country is CountryCode.US)
    jp = next(source for source in sources if source.country is CountryCode.JP)
    assert "Ticker Report" in us.blocked_publishers
    assert "Pr Times" in jp.blocked_publishers
    assert {"金融", "半導体", "物価"} <= set(jp.required_title_terms)
    assert us.availability_delay_hours == 12
    assert us.max_pages_per_collection == 15
    assert jp.availability_delay_hours == 12
    assert jp.max_pages_per_collection == 25
    assert jp.excluded_domains == ("investing.com",)
