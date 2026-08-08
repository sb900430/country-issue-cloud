from collections.abc import Callable, Mapping
from datetime import date, datetime
from pathlib import Path

from app.batch.collection import CollectionRunner
from app.batch.collectors.base import Collector
from app.batch.collectors.gdelt import GdeltCollector, GdeltSource, RequestIntervalGate
from app.batch.collectors.naver import NaverCollector, NaverSource
from app.batch.collectors.rss import RssCollector, RssSource
from app.batch.issues import MockIssueExtractor
from app.batch.keyword_pipeline import build_keyword_result
from app.batch.keyword_publishing import KeywordStaticJsonPublisher
from app.batch.naver_usage import NaverUsageLedger, NaverUsagePolicy
from app.batch.pipeline import IssuePipeline, PipelineLock
from app.batch.publishing import StaticJsonPublisher
from app.core.settings import AppMode
from app.repositories.json_issue_repository import JsonIssueRepository
from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.issues import CountryCode, IssueResult, IssueStatus
from app.schemas.keywords import KeywordResult


def run_live_batch(
    rss_sources: list[RssSource],
    gdelt_sources: list[GdeltSource],
    naver_sources: list[NaverSource],
    fetch: Callable[[str], bytes],
    authenticated_fetch: Callable[[str, Mapping[str, str]], bytes],
    naver_client_id: str | None,
    naver_client_secret: str | None,
    window_start: datetime,
    window_end: datetime,
    target_date: date,
    data_dir: Path,
    site_data_dir: Path,
) -> IssueResult:
    gdelt_request_gate = RequestIntervalGate(minimum_interval_seconds=60.0)
    collectors: list[Collector] = [
        *[GdeltCollector(source, fetch, gdelt_request_gate) for source in gdelt_sources],
        *[RssCollector(source, fetch) for source in rss_sources],
    ]
    if naver_sources:
        if not naver_client_id or not naver_client_secret:
            raise ValueError("NAVER credentials are required when NAVER is enabled")
        usage_ledger = NaverUsageLedger(
            data_dir / "runtime" / "naver-usage.json",
            NaverUsagePolicy(),
        )
        collectors.extend(
            NaverCollector(
                source,
                authenticated_fetch,
                naver_client_id,
                naver_client_secret,
                usage_ledger,
            )
            for source in naver_sources
        )
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


def run_live_keyword_batch(
    rss_sources: list[RssSource],
    gdelt_sources: list[GdeltSource],
    naver_sources: list[NaverSource],
    fetch: Callable[[str], bytes],
    authenticated_fetch: Callable[[str, Mapping[str, str]], bytes],
    naver_client_id: str | None,
    naver_client_secret: str | None,
    window_start: datetime,
    window_end: datetime,
    target_date: date,
    data_dir: Path,
    site_data_dir: Path,
) -> KeywordResult:
    gdelt_request_gate = RequestIntervalGate(minimum_interval_seconds=60.0)
    collectors: list[Collector] = [
        *[GdeltCollector(source, fetch, gdelt_request_gate) for source in gdelt_sources],
        *[RssCollector(source, fetch) for source in rss_sources],
    ]
    if naver_sources:
        if not naver_client_id or not naver_client_secret:
            raise ValueError("NAVER credentials are required when NAVER is enabled")
        usage_ledger = NaverUsageLedger(
            data_dir / "runtime" / "naver-usage.json", NaverUsagePolicy()
        )
        collectors.extend(
            NaverCollector(
                source,
                authenticated_fetch,
                naver_client_id,
                naver_client_secret,
                usage_ledger,
            )
            for source in naver_sources
        )
    collections = CollectionRunner(collectors).collect_all(
        tuple(CountryCode), window_start, window_end, mode=AppMode.LIVE
    )
    result = build_keyword_result(target_date, collections)
    if result.status is IssueStatus.SUCCESS:
        repository = JsonKeywordRepository(data_dir)
        repository.save(result)
        KeywordStaticJsonPublisher(repository.published_dir, site_data_dir).publish()
    return result
