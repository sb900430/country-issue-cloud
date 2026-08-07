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
            articles, errors = self._collect_sources(fixtures, window_start, window_end)
            used_fallback = False
        elif mode == AppMode.LIVE:
            articles, errors = self._collect_sources(live, window_start, window_end)
            used_fallback = False
        else:
            articles, errors = self._collect_sources(live, window_start, window_end)
            used_fallback = not articles
            if used_fallback:
                fallback_articles, fallback_errors = self._collect_sources(
                    fixtures, window_start, window_end
                )
                articles.extend(fallback_articles)
                errors.extend(fallback_errors)
        unique_articles = deduplicate_articles(articles)
        selected_articles = select_diverse_articles(
            unique_articles, self.max_articles_per_country
        )
        return CountryCollectionResult(
            country=country,
            articles=tuple(selected_articles),
            errors=tuple(errors),
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
    ) -> tuple[list[CollectedArticle], list[str]]:
        articles: list[CollectedArticle] = []
        errors: list[str] = []
        for collector in collectors:
            try:
                articles.extend(
                    collector.collect(
                        window_start, window_end, self.max_articles_per_country
                    )
                )
            except Exception as error:
                errors.append(f"{collector.source_id}:{type(error).__name__}")
        return articles, errors
