import argparse
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.batch.http_client import HttpsFeedClient
from app.batch.keyword_fixture import publish_keyword_fixture
from app.batch.keyword_history import restore_keyword_history
from app.batch.keyword_publishing import KeywordStaticJsonPublisher
from app.batch.keywords import KeywordRanker
from app.batch.live import run_live_batch, run_live_keyword_batch
from app.batch.publishing import StaticJsonPublisher
from app.batch.semantic_keywords import build_local_semantic_grouper
from app.batch.source_config import (
    load_gdelt_sources,
    load_naver_sources,
    load_newsdata_sources,
    load_rss_sources,
    load_source_registry,
)
from app.core.settings import get_settings
from app.repositories.json_issue_repository import JsonIssueRepository
from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.issues import IssueResult


def resolve_collection_window(
    target_date: date, now: datetime, lookback_hours: int
) -> tuple[datetime, datetime]:
    jst = ZoneInfo("Asia/Tokyo")
    target_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time(), jst)
    window_end = min(now, target_end.astimezone(UTC))
    return window_end - timedelta(hours=lookback_hours), window_end


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="country-issue-cloud-batch")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fixture = subparsers.add_parser("publish-fixture")
    fixture.add_argument("--fixture", type=Path, required=True)
    fixture.add_argument("--data-dir", type=Path, required=True)
    fixture.add_argument("--site-data-dir", type=Path, required=True)
    live = subparsers.add_parser("publish-live")
    live.add_argument("--sources-config", type=Path, required=True)
    live.add_argument("--data-dir", type=Path, required=True)
    live.add_argument("--site-data-dir", type=Path, required=True)
    live.add_argument("--target-date", type=date.fromisoformat)
    live.add_argument("--lookback-hours", type=int, default=48)
    live.add_argument("--enable-gdelt", action="store_true")
    live.add_argument("--enable-naver", action="store_true")
    live.add_argument("--enable-newsdata", action="store_true")
    keyword_fixture = subparsers.add_parser("publish-keyword-fixture")
    keyword_fixture.add_argument("--evaluation-dir", type=Path, required=True)
    keyword_fixture.add_argument("--data-dir", type=Path, required=True)
    keyword_fixture.add_argument("--site-data-dir", type=Path, required=True)
    keyword_live = subparsers.add_parser("publish-keyword-live")
    keyword_live.add_argument("--sources-config", type=Path, required=True)
    keyword_live.add_argument("--data-dir", type=Path, required=True)
    keyword_live.add_argument("--site-data-dir", type=Path, required=True)
    keyword_live.add_argument("--target-date", type=date.fromisoformat)
    keyword_live.add_argument("--lookback-hours", type=int, default=24)
    keyword_live.add_argument("--skip-rss", action="store_true")
    keyword_live.add_argument("--single-attempt", action="store_true")
    keyword_live.add_argument("--enable-newsdata", action="store_true")
    restore_history = subparsers.add_parser("restore-keyword-history")
    restore_history.add_argument("--base-url", required=True)
    restore_history.add_argument("--data-dir", type=Path, required=True)
    restore_history.add_argument("--target-date", type=date.fromisoformat, required=True)
    restore_history.add_argument("--include-latest", action="store_true")
    publish_existing = subparsers.add_parser("publish-existing-keyword-data")
    publish_existing.add_argument("--data-dir", type=Path, required=True)
    publish_existing.add_argument("--site-data-dir", type=Path, required=True)
    return parser


def main() -> int:
    parser = _build_parser()
    arguments = parser.parse_args()

    if arguments.command == "publish-fixture":
        result = IssueResult.model_validate_json(arguments.fixture.read_text(encoding="utf-8"))
        repository = JsonIssueRepository(arguments.data_dir)
        repository.save(result)
        publisher = StaticJsonPublisher(arguments.data_dir / "published", arguments.site_data_dir)
        outputs = publisher.publish()
        print(f"published {len(outputs)} validated JSON files")
        return 0
    if arguments.command == "publish-live":
        if arguments.lookback_hours < 1 or arguments.lookback_hours > 168:
            parser.error("--lookback-hours must be between 1 and 168")
        now = datetime.now(UTC)
        target_date = arguments.target_date or datetime.now(ZoneInfo("Asia/Tokyo")).date()
        window_start, window_end = resolve_collection_window(
            target_date, now, arguments.lookback_hours
        )
        client = HttpsFeedClient()
        settings = get_settings()
        registry = load_source_registry(arguments.sources_config)
        result = run_live_batch(
            load_rss_sources(registry),
            (load_gdelt_sources(registry) if arguments.enable_gdelt else []),
            (load_naver_sources(registry) if arguments.enable_naver else []),
            (load_newsdata_sources(registry) if arguments.enable_newsdata else []),
            client.fetch,
            client.fetch_with_headers,
            settings.naver_client_id,
            settings.naver_client_secret,
            settings.newsdata_api_key,
            window_start,
            window_end,
            target_date,
            arguments.data_dir,
            arguments.site_data_dir,
        )
        print(
            f"live batch {result.status.value}: "
            + ", ".join(
                f"{country.value}={result.countries[country].article_count}"
                + (
                    f"[{','.join(result.countries[country].warnings)}]"
                    if result.countries[country].warnings
                    else ""
                )
                for country in result.countries
            )
        )
        return 0 if result.status.value != "failed" else 1
    if arguments.command == "publish-keyword-fixture":
        keyword_result = publish_keyword_fixture(
            arguments.evaluation_dir, arguments.data_dir, arguments.site_data_dir
        )
        print(f"published keyword fixture: {keyword_result.status.value}")
        return 0
    if arguments.command == "publish-keyword-live":
        if arguments.lookback_hours < 1 or arguments.lookback_hours > 168:
            parser.error("--lookback-hours must be between 1 and 168")
        now = datetime.now(UTC)
        target_date = arguments.target_date or datetime.now(ZoneInfo("Asia/Tokyo")).date()
        window_start, window_end = resolve_collection_window(
            target_date, now, arguments.lookback_hours
        )
        client = HttpsFeedClient(max_attempts=1 if arguments.single_attempt else 2)
        settings = get_settings()
        registry = load_source_registry(arguments.sources_config)
        keyword_result = run_live_keyword_batch(
            ([] if arguments.skip_rss else load_rss_sources(registry)),
            load_gdelt_sources(registry),
            load_naver_sources(registry),
            (load_newsdata_sources(registry) if arguments.enable_newsdata else []),
            client.fetch,
            client.fetch_with_headers,
            settings.naver_client_id,
            settings.naver_client_secret,
            settings.newsdata_api_key,
            window_start,
            window_end,
            target_date,
            arguments.data_dir,
            arguments.site_data_dir,
            KeywordRanker(semantic_grouper=build_local_semantic_grouper()),
        )
        print(
            f"keyword live batch {keyword_result.status.value}: "
            + ", ".join(
                f"{country.value}={keyword_result.countries[country].article_count}"
                for country in keyword_result.countries
            )
        )
        return (
            0
            if keyword_result.status.value != "failed"
            or (arguments.site_data_dir / "latest.json").exists()
            else 1
        )
    if arguments.command == "restore-keyword-history":
        restored = restore_keyword_history(
            arguments.base_url,
            JsonKeywordRepository(arguments.data_dir),
            arguments.target_date,
            HttpsFeedClient(max_attempts=2, retry_delay_seconds=5).fetch,
            include_latest=arguments.include_latest,
        )
        print(f"restored keyword history: {len(restored)} dates")
        return 0
    if arguments.command == "publish-existing-keyword-data":
        keyword_repository = JsonKeywordRepository(arguments.data_dir)
        outputs = KeywordStaticJsonPublisher(
            keyword_repository.published_dir, arguments.site_data_dir
        ).publish()
        print(f"published existing keyword data: {len(outputs)} files")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
