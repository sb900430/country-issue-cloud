from pathlib import Path

import pytest

from app.batch.source_config import load_rss_sources
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
