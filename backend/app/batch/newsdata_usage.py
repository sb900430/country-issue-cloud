from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.batch.usage_ledger import JsonUsageLedger


class NewsDataUsageLimitExceededError(RuntimeError):
    pass


@dataclass(frozen=True)
class NewsDataUsagePolicy:
    daily_limit: int = 40
    monthly_limit: int = 1_200
    paid_overage_enabled: bool = False

    def validate(self) -> None:
        if self.daily_limit < 1 or self.daily_limit > 200:
            raise ValueError("NewsData daily limit must remain within the free quota")
        if self.monthly_limit < 1:
            raise ValueError("NewsData monthly limit must be positive")
        if self.paid_overage_enabled:
            raise ValueError("paid NewsData overage requires an explicit policy change")

    def ensure_request_allowed(self, *, daily_usage: int, monthly_usage: int) -> None:
        self.validate()
        if daily_usage >= self.daily_limit:
            raise NewsDataUsageLimitExceededError("daily NewsData request limit reached")
        if monthly_usage >= self.monthly_limit:
            raise NewsDataUsageLimitExceededError("monthly NewsData request limit reached")


class NewsDataUsageLedger(JsonUsageLedger):
    def __init__(
        self,
        path: Path,
        policy: NewsDataUsagePolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(
            path,
            policy,
            ZoneInfo("Asia/Tokyo"),
            "Invalid NewsData usage ledger",
            clock,
        )
