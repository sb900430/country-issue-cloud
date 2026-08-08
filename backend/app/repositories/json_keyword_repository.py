import re
from collections.abc import Callable
from contextlib import suppress
from datetime import date, datetime
from os import replace
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from app.repositories.base import RepositoryDataError
from app.schemas.keywords import KeywordResult

KEYWORD_FILE_PATTERN = re.compile(r"^keywords_(\d{4}-\d{2}-\d{2})\.json$")


class JsonKeywordRepository:
    def __init__(self, data_dir: Path, today_provider: Callable[[], date] | None = None) -> None:
        self._published_dir = data_dir / "keyword-published"
        self._today_provider = today_provider or (
            lambda: datetime.now(tz=ZoneInfo("Asia/Tokyo")).date()
        )

    @property
    def published_dir(self) -> Path:
        return self._published_dir

    def find_by_date(self, target_date: date) -> KeywordResult | None:
        return self._read(self._published_dir / f"keywords_{target_date.isoformat()}.json")

    def find_latest(self) -> KeywordResult | None:
        return self._read(self._published_dir / "latest.json")

    def find_available_dates(self, within_days: int) -> list[date]:
        if within_days < 1:
            raise ValueError("within_days must be at least 1")
        if not self._published_dir.exists():
            return []
        today = self._today_provider()
        values: list[date] = []
        for path in self._published_dir.iterdir():
            match = KEYWORD_FILE_PATTERN.fullmatch(path.name)
            if match is None or not path.is_file():
                continue
            try:
                value = date.fromisoformat(match.group(1))
            except ValueError:
                continue
            if 0 <= (today - value).days < within_days:
                values.append(value)
        return sorted(values, reverse=True)

    def save(self, result: KeywordResult) -> None:
        self._published_dir.mkdir(parents=True, exist_ok=True)
        content = result.model_dump_json(indent=2)
        self._atomic_write(
            self._published_dir / f"keywords_{result.date.isoformat()}.json", content
        )
        self._atomic_write(self._published_dir / "latest.json", content)

    def _read(self, path: Path) -> KeywordResult | None:
        if not path.exists():
            return None
        try:
            return KeywordResult.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError, ValueError) as error:
            raise RepositoryDataError(f"Invalid keyword data: {path.name}") from error

    @staticmethod
    def _atomic_write(destination: Path, content: str) -> None:
        temporary = destination.with_name(f".{destination.name}.tmp")
        try:
            temporary.write_text(content, encoding="utf-8")
            replace(temporary, destination)
        except OSError as error:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise RepositoryDataError(f"Failed to save keyword data: {destination.name}") from error
