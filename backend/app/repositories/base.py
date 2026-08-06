from datetime import date
from typing import Protocol

from app.schemas.issues import IssueResult


class RepositoryDataError(RuntimeError):
    pass


class IssueRepository(Protocol):
    def find_by_date(self, target_date: date) -> IssueResult | None: ...

    def find_latest(self) -> IssueResult | None: ...

    def find_available_dates(self, within_days: int) -> list[date]: ...

    def save(self, result: IssueResult) -> None: ...

    def delete_expired(self, retention_days: int) -> int: ...
