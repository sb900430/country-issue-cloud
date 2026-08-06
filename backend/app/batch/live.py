from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from app.batch.collection import CollectionRunner
from app.batch.collectors.base import Collector
from app.batch.collectors.rss import RssCollector, RssSource
from app.batch.issues import MockIssueExtractor
from app.batch.pipeline import IssuePipeline, PipelineLock
from app.batch.publishing import StaticJsonPublisher
from app.core.settings import AppMode
from app.repositories.json_issue_repository import JsonIssueRepository
from app.schemas.issues import CountryCode, IssueResult, IssueStatus


def run_live_batch(
    sources: list[RssSource],
    fetch: Callable[[str], bytes],
    window_start: datetime,
    window_end: datetime,
    target_date: date,
    data_dir: Path,
    site_data_dir: Path,
) -> IssueResult:
    collectors: list[Collector] = [RssCollector(source, fetch) for source in sources]
    collections = CollectionRunner(collectors).collect_all(
        tuple(CountryCode), window_start, window_end, mode=AppMode.LIVE
    )
    repository = JsonIssueRepository(data_dir)
    pipeline = IssuePipeline(
        repository,
        MockIssueExtractor(),
        PipelineLock(data_dir / "runtime" / "pipeline.lock"),
    )
    result = pipeline.run(target_date, collections)
    if result.status != IssueStatus.FAILED:
        StaticJsonPublisher(data_dir / "published", site_data_dir).publish()
    return result
