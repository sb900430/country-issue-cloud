import argparse
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.batch.http_client import HttpsFeedClient
from app.batch.live import run_live_batch
from app.batch.publishing import StaticJsonPublisher
from app.batch.source_config import load_rss_sources
from app.repositories.json_issue_repository import JsonIssueRepository
from app.schemas.issues import IssueResult


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
    arguments = parser.parse_args()

    if arguments.command == "publish-fixture":
        result = IssueResult.model_validate_json(arguments.fixture.read_text(encoding="utf-8"))
        repository = JsonIssueRepository(arguments.data_dir)
        repository.save(result)
        publisher = StaticJsonPublisher(
            arguments.data_dir / "published", arguments.site_data_dir
        )
        outputs = publisher.publish()
        print(f"published {len(outputs)} validated JSON files")
        return 0
    if arguments.command == "publish-live":
        if arguments.lookback_hours < 1 or arguments.lookback_hours > 168:
            parser.error("--lookback-hours must be between 1 and 168")
        now = datetime.now(UTC)
        target_date = arguments.target_date or datetime.now(ZoneInfo("Asia/Tokyo")).date()
        target_end = datetime.combine(
            target_date + timedelta(days=1), datetime.min.time(), UTC
        )
        window_end = min(now, target_end)
        window_start = window_end - timedelta(hours=arguments.lookback_hours)
        client = HttpsFeedClient()
        result = run_live_batch(
            load_rss_sources(arguments.sources_config),
            client.fetch,
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
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
