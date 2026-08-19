from pathlib import Path
from typing import Any

from app.batch.static_publishing import publish_static_history
from app.schemas.issues import IssueStatus
from app.schemas.keywords import KeywordResult


class KeywordStaticJsonPublisher:
    def __init__(self, published_dir: Path, site_data_dir: Path) -> None:
        self.published_dir = published_dir
        self.site_data_dir = site_data_dir

    def publish(self) -> list[Path]:
        return publish_static_history(
            self.published_dir,
            self.site_data_dir,
            "keywords_????-??-??.json",
            self._validate,
            "latest keyword result has no matching dated result",
            self._public_status_files,
        )

    @staticmethod
    def _validate(path: Path) -> KeywordResult:
        return KeywordResult.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def _public_status_files(
        latest: KeywordResult, history: list[KeywordResult]
    ) -> dict[str, Any]:
        calendar = [
            KeywordStaticJsonPublisher._calendar_entry(result)
            for result in reversed(history)
        ]
        current = history[-1]
        return {
            "calendar.json": {"schema_version": "1.0", "days": calendar},
            "status.json": {
                "schema_version": "1.0",
                "attempted_date": current.date.isoformat(),
                "generated_at": current.generated_at.isoformat(),
                "status": current.status.value,
                "displayed_date": latest.date.isoformat(),
                "countries": KeywordStaticJsonPublisher._country_statuses(current),
            },
        }

    @staticmethod
    def _calendar_entry(result: KeywordResult) -> dict[str, Any]:
        return {
            "date": result.date.isoformat(),
            "status": result.status.value,
            "countries": KeywordStaticJsonPublisher._country_statuses(result),
        }

    @staticmethod
    def _country_statuses(result: KeywordResult) -> dict[str, Any]:
        return {
            country.value: {
                "status": value.status.value,
                "article_count": value.article_count,
                "reason": KeywordStaticJsonPublisher._failure_reason(
                    value.status, value.article_count
                ),
            }
            for country, value in result.countries.items()
        }

    @staticmethod
    def _failure_reason(status: IssueStatus, article_count: int) -> str | None:
        if status is IssueStatus.SUCCESS:
            return None
        if article_count < 50:
            return "insufficient_articles"
        return "insufficient_keywords"
