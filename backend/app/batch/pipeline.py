from contextlib import AbstractContextManager
from datetime import UTC, date, datetime
from pathlib import Path
from types import TracebackType

from app.batch.issues import IssueExtractor, aggregate_top_issues
from app.batch.models import CountryCollectionResult
from app.repositories.base import IssueRepository
from app.schemas.issues import CountryCode, CountryIssueResult, IssueResult, IssueStatus


class PipelineLockedError(RuntimeError):
    pass


class PipelineLock(AbstractContextManager["PipelineLock"]):
    def __init__(self, path: Path) -> None:
        self.path = path
        self._acquired = False

    def __enter__(self) -> "PipelineLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("x", encoding="utf-8") as lock_file:
                lock_file.write(str(datetime.now(UTC)))
        except FileExistsError as error:
            raise PipelineLockedError("pipeline is already running") from error
        self._acquired = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._acquired:
            self.path.unlink(missing_ok=True)
            self._acquired = False


class IssuePipeline:
    def __init__(
        self,
        repository: IssueRepository,
        extractor: IssueExtractor,
        lock: PipelineLock,
    ) -> None:
        self.repository = repository
        self.extractor = extractor
        self.lock = lock

    def run(
        self,
        target_date: date,
        collections: dict[CountryCode, CountryCollectionResult],
        dry_run: bool = False,
    ) -> IssueResult:
        with self.lock:
            countries = {
                country: self._process_country(country, collections.get(country))
                for country in CountryCode
            }
            publishable = sum(
                result.status in {IssueStatus.SUCCESS, IssueStatus.PARTIAL_SUCCESS}
                for result in countries.values()
            )
            if publishable == 3 and all(
                result.status == IssueStatus.SUCCESS for result in countries.values()
            ):
                status = IssueStatus.SUCCESS
            elif publishable >= 2:
                status = IssueStatus.PARTIAL_SUCCESS
            else:
                status = IssueStatus.FAILED
            result = IssueResult(
                schema_version="1.0",
                date=target_date,
                generated_at=datetime.now(UTC),
                status=status,
                countries=countries,
            )
            if status != IssueStatus.FAILED and not dry_run:
                self.repository.save(result)
            return result

    def _process_country(
        self,
        country: CountryCode,
        collection: CountryCollectionResult | None,
    ) -> CountryIssueResult:
        if collection is None:
            return self._failed_country("collection_unavailable")
        if not collection.articles:
            return self._failed_country(
                "collection_unavailable", additional_warnings=list(collection.errors)
            )
        try:
            articles = list(collection.articles)
            extraction = self.extractor.extract(country, articles)
            result = aggregate_top_issues(country, articles, extraction)
            if collection.errors:
                return result.model_copy(
                    update={"warnings": [*result.warnings, *collection.errors]}
                )
            return result
        except (OSError, RuntimeError, ValueError) as error:
            return self._failed_country(f"pipeline_failed:{type(error).__name__}")

    @staticmethod
    def _failed_country(
        warning: str, additional_warnings: list[str] | None = None
    ) -> CountryIssueResult:
        return CountryIssueResult(
            status=IssueStatus.FAILED,
            article_count=0,
            extraction_success_rate=0,
            top_issues=[],
            warnings=[warning, *(additional_warnings or [])],
        )
