import re
from collections.abc import Callable
from contextlib import suppress
from datetime import date, datetime
from os import replace
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from app.repositories.base import RepositoryDataError
from app.schemas.issues import IssueResult

ISSUE_FILE_PATTERN = re.compile(r"^issues_(\d{4}-\d{2}-\d{2})\.json$")


class JsonIssueRepository:
    def __init__(
        self,
        data_dir: Path,
        today_provider: Callable[[], date] | None = None,
    ) -> None:
        self._published_dir = data_dir / "published"
        self._today_provider = today_provider or (
            lambda: datetime.now(tz=ZoneInfo("Asia/Tokyo")).date()
        )

    def find_by_date(self, target_date: date) -> IssueResult | None:
        return self._read(self._published_dir / f"issues_{target_date.isoformat()}.json")

    def find_latest(self) -> IssueResult | None:
        return self._read(self._published_dir / "latest.json")

    def find_available_dates(self, within_days: int) -> list[date]:
        if within_days < 1:
            raise ValueError("within_days must be at least 1")
        if not self._published_dir.exists():
            return []

        today = self._today_provider()
        available_dates: list[date] = []
        for path in self._published_dir.iterdir():
            match = ISSUE_FILE_PATTERN.fullmatch(path.name)
            if match is None or not path.is_file():
                continue
            try:
                published_date = date.fromisoformat(match.group(1))
            except ValueError:
                continue
            age_in_days = (today - published_date).days
            if 0 <= age_in_days < within_days:
                available_dates.append(published_date)

        return sorted(available_dates, reverse=True)

    def save(self, result: IssueResult) -> None:
        self._published_dir.mkdir(parents=True, exist_ok=True)
        serialized = result.model_dump_json(indent=2)
        dated_path = self._published_dir / f"issues_{result.date.isoformat()}.json"
        self._atomic_write(dated_path, serialized)
        self._atomic_write(self._published_dir / "latest.json", serialized)

    def delete_expired(self, retention_days: int) -> int:
        if retention_days < 1:
            raise ValueError("retention_days must be at least 1")
        if not self._published_dir.exists():
            return 0

        today = self._today_provider()
        deleted_count = 0
        for path in self._published_dir.iterdir():
            match = ISSUE_FILE_PATTERN.fullmatch(path.name)
            if match is None or not path.is_file():
                continue
            try:
                published_date = date.fromisoformat(match.group(1))
            except ValueError:
                continue
            if (today - published_date).days < retention_days:
                continue
            try:
                path.unlink()
            except OSError as error:
                raise RepositoryDataError(f"Failed to delete issue data: {path.name}") from error
            deleted_count += 1
        return deleted_count

    def _read(self, path: Path) -> IssueResult | None:
        if not path.exists():
            return None
        try:
            return IssueResult.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError, ValueError) as error:
            raise RepositoryDataError(f"Invalid issue data: {path.name}") from error

    def _atomic_write(self, destination: Path, content: str) -> None:
        temporary = destination.with_name(f".{destination.name}.tmp")
        try:
            temporary.write_text(content, encoding="utf-8")
            replace(temporary, destination)
        except OSError as error:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise RepositoryDataError(f"Failed to save issue data: {destination.name}") from error
