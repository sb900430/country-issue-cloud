import argparse
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.batch.http_client import HttpsFeedClient
from app.batch.keyword_fixture import publish_keyword_fixture
from app.batch.live import run_live_batch, run_live_keyword_batch
from app.batch.publishing import StaticJsonPublisher
from app.batch.source_config import load_gdelt_sources, load_naver_sources, load_rss_sources
from app.core.settings import get_settings
from app.repositories.json_issue_repository import JsonIssueRepository
from app.schemas.issues import IssueResult


def resolve_collection_window(
    target_date: date, now: datetime, lookback_hours: int
) -> tuple[datetime, datetime]:
    jst = ZoneInfo("Asia/Tokyo")
    target_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time(), jst)
    window_end = min(now, target_end.astimezone(UTC))
    return window_end - timedelta(hours=lookback_hours), window_end


def main() -> int:
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
        result = run_live_batch(
            load_rss_sources(arguments.sources_config),
            (load_gdelt_sources(arguments.sources_config) if arguments.enable_gdelt else []),
            (load_naver_sources(arguments.sources_config) if arguments.enable_naver else []),
            client.fetch,
            client.fetch_with_headers,
            settings.naver_client_id,
            settings.naver_client_secret,
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
        keyword_result = run_live_keyword_batch(
            ([] if arguments.skip_rss else load_rss_sources(arguments.sources_config)),
            load_gdelt_sources(arguments.sources_config),
            load_naver_sources(arguments.sources_config),
            client.fetch,
            client.fetch_with_headers,
            settings.naver_client_id,
            settings.naver_client_secret,
            window_start,
            window_end,
            target_date,
            arguments.data_dir,
            arguments.site_data_dir,
        )
        print(
            f"keyword live batch {keyword_result.status.value}: "
            + ", ".join(
                f"{country.value}={keyword_result.countries[country].article_count}"
                for country in keyword_result.countries
            )
        )
        return 0 if keyword_result.status.value == "success" else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
