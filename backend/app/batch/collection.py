from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from app.batch.collectors.base import Collector
from app.batch.deduplication import deduplicate_articles, select_diverse_articles
from app.batch.models import CollectedArticle, CollectorKind, CountryCollectionResult
from app.core.settings import AppMode
from app.schemas.issues import CountryCode


class CollectionRunner:
    def __init__(self, collectors: list[Collector], max_articles_per_country: int = 250) -> None:
        self.collectors = collectors
        self.max_articles_per_country = max_articles_per_country

    def collect_all(
        self,
        countries: tuple[CountryCode, ...],
        window_start: datetime,
        window_end: datetime,
        mode: AppMode,
    ) -> dict[CountryCode, CountryCollectionResult]:
        with ThreadPoolExecutor(max_workers=len(countries)) as executor:
            futures = {
                executor.submit(
                    self._collect_country, country, window_start, window_end, mode
                ): country
                for country in countries
            }
            results: dict[CountryCode, CountryCollectionResult] = {}
            for future in as_completed(futures):
                country = futures[future]
                try:
                    results[country] = future.result()
                except Exception as error:
                    results[country] = CountryCollectionResult(
                        country=country,
                        errors=(f"country_collection_failed:{type(error).__name__}",),
                        collected_at=datetime.now(UTC),
                    )
        return results

    def _collect_country(
        self,
        country: CountryCode,
        window_start: datetime,
        window_end: datetime,
        mode: AppMode,
    ) -> CountryCollectionResult:
        fixtures = self._for_country(country, CollectorKind.FIXTURE)
        live = self._for_country(country, CollectorKind.LIVE)
        if mode == AppMode.FIXTURE:
            (
                articles,
                errors,
                source_counts,
                source_filter_counts,
                source_publisher_counts,
            ) = self._collect_sources(fixtures, window_start, window_end)
            used_fallback = False
        elif mode == AppMode.LIVE:
            (
                articles,
                errors,
                source_counts,
                source_filter_counts,
                source_publisher_counts,
            ) = self._collect_sources(live, window_start, window_end)
            used_fallback = False
        else:
            (
                articles,
                errors,
                source_counts,
                source_filter_counts,
                source_publisher_counts,
            ) = self._collect_sources(live, window_start, window_end)
            used_fallback = not articles
            if used_fallback:
                (
                    fallback_articles,
                    fallback_errors,
                    fallback_counts,
                    fallback_filter_counts,
                    fallback_publisher_counts,
                ) = self._collect_sources(fixtures, window_start, window_end)
                articles.extend(fallback_articles)
                errors.extend(fallback_errors)
                source_counts.update(fallback_counts)
                source_filter_counts.update(fallback_filter_counts)
                source_publisher_counts.update(fallback_publisher_counts)
        unique_articles = deduplicate_articles(articles)
        selected_articles = select_diverse_articles(unique_articles, self.max_articles_per_country)
        return CountryCollectionResult(
            country=country,
            articles=tuple(selected_articles),
            errors=tuple(errors),
            source_article_counts=source_counts,
            source_filter_counts=source_filter_counts,
            source_publisher_counts=source_publisher_counts,
            source_rejected_domain_counts={
                collector.source_id: dict(rejected_domains)
                for collector in [*fixtures, *live]
                if isinstance(
                    (rejected_domains := getattr(collector, "last_rejected_domain_counts", None)),
                    dict,
                )
                and rejected_domains
            },
            raw_article_count=len(articles),
            deduplicated_article_count=len(unique_articles),
            used_fixture_fallback=used_fallback,
            collected_at=datetime.now(UTC),
        )

    def _for_country(self, country: CountryCode, kind: CollectorKind) -> list[Collector]:
        return [
            collector
            for collector in self.collectors
            if collector.country == country and collector.kind == kind
        ]

    def _collect_sources(
        self, collectors: list[Collector], window_start: datetime, window_end: datetime
    ) -> tuple[
        list[CollectedArticle],
        list[str],
        dict[str, int],
        dict[str, dict[str, int]],
        dict[str, dict[str, int]],
    ]:
        articles: list[CollectedArticle] = []
        errors: list[str] = []
        source_counts: dict[str, int] = {}
        source_filter_counts: dict[str, dict[str, int]] = {}
        source_publisher_counts: dict[str, dict[str, int]] = {}
        for collector in collectors:
            try:
                collected = collector.collect(
                    window_start, window_end, self.max_articles_per_country
                )
                articles.extend(collected)
                source_counts[collector.source_id] = len(collected)
                source_publisher_counts[collector.source_id] = dict(
                    sorted(Counter(article.publisher for article in collected).items())
                )
                diagnostics = getattr(collector, "last_diagnostics", None)
                if isinstance(diagnostics, dict):
                    source_filter_counts[collector.source_id] = dict(diagnostics)
            except Exception as error:
                category = getattr(error, "category", None)
                category_suffix = f":{category}" if isinstance(category, str) else ""
                errors.append(
                    f"{collector.source_id}:{type(error).__name__}{category_suffix}"
                )
                source_counts[collector.source_id] = 0
                source_publisher_counts[collector.source_id] = {}
                diagnostics = getattr(collector, "last_diagnostics", None)
                if isinstance(diagnostics, dict):
                    source_filter_counts[collector.source_id] = dict(diagnostics)
        return articles, errors, source_counts, source_filter_counts, source_publisher_counts
