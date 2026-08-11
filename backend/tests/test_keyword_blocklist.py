from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.batch.keyword_blocklist import KeywordBlocklist
from app.batch.keywords import KeywordRanker
from app.batch.models import CollectedArticle
from app.schemas.issues import CountryCode


def _article(index: int, title: str) -> CollectedArticle:
    return CollectedArticle(
        article_id=f"article-{index:03d}",
        country=CountryCode.KR,
        title=title,
        url=f"https://example.com/article-{index:03d}",
        publisher=f"publisher-{index % 5}",
        published_at=datetime(2026, 8, 11, tzinfo=UTC) + timedelta(minutes=index),
    )


def test_repository_blocklist_excludes_configured_political_terms() -> None:
    blocklist = KeywordBlocklist.load()

    assert blocklist.blocks(CountryCode.KR, "국힘")
    assert blocklist.blocks(CountryCode.KR, "오세훈시장")
    assert not blocklist.blocks(CountryCode.JP, "オ・セフン")
    assert not blocklist.blocks(CountryCode.KR, "코스닥")


def test_exact_and_disabled_rules_do_not_overblock(tmp_path: Path) -> None:
    path = tmp_path / "keyword-blocklist.yml"
    path.write_text(
        """schema_version: "1.0"
countries:
  US: []
  JP: []
  KR:
    - term: "국힘"
      match: "exact"
      category: "politics"
      reason_ko: "정당 약칭"
      reason_ja: "政党略称"
      added_on: "2026-08-11"
      enabled: true
    - term: "오세훈"
      match: "contains"
      category: "politics"
      reason_ko: "정치인 이름"
      reason_ja: "政治家名"
      added_on: "2026-08-11"
      enabled: false
""",
        encoding="utf-8",
    )
    blocklist = KeywordBlocklist.load(path)

    assert blocklist.blocks(CountryCode.KR, "국힘")
    assert not blocklist.blocks(CountryCode.KR, "국힘정책")
    assert not blocklist.blocks(CountryCode.KR, "오세훈시장")


def test_ranker_removes_blocked_terms_before_ranking() -> None:
    topics = ("오세훈", "반도체", "기준금리", "원화변동성", "부동산대출", "소비자물가")
    articles = [
        _article(index, f"{topics[index % len(topics)]} {index:03d}")
        for index in range(120)
    ]

    result = KeywordRanker().analyze(CountryCode.KR, articles)

    labels = {keyword.label for keyword in result.top_keywords}
    assert "오세훈" not in labels
    assert labels == {"반도체", "기준금리", "원화변동성", "부동산대출", "소비자물가"}


def test_invalid_or_incomplete_blocklist_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "keyword-blocklist.yml"
    path.write_text(
        'schema_version: "1.0"\ncountries:\n  KR: []\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid keyword blocklist"):
        KeywordBlocklist.load(path)
