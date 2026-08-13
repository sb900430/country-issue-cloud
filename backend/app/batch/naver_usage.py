from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.batch.usage_ledger import JsonUsageLedger


class NaverUsageLimitExceededError(RuntimeError):
    pass


class NaverPaidOverageDisabledError(RuntimeError):
    pass


@dataclass(frozen=True)
class NaverUsagePolicy:
    daily_limit: int = 300
    monthly_limit: int = 9_000
    alert_thresholds: tuple[int, int] = (50, 80)
    paid_overage_enabled: bool = False

    def validate(self) -> None:
        if self.daily_limit < 1 or self.monthly_limit < 1:
            raise ValueError("NAVER usage limits must be positive")
        if self.alert_thresholds != (50, 80):
            raise ValueError("NAVER alert thresholds must remain at 50% and 80%")
        if self.paid_overage_enabled:
            raise NaverPaidOverageDisabledError(
                "paid NAVER overage requires an explicit policy change"
            )

    def ensure_request_allowed(self, *, daily_usage: int, monthly_usage: int) -> None:
        self.validate()
        if daily_usage >= self.daily_limit:
            raise NaverUsageLimitExceededError("daily NAVER request limit reached")
        if monthly_usage >= self.monthly_limit:
            raise NaverUsageLimitExceededError("monthly NAVER request limit reached")


class NaverUsageLedger(JsonUsageLedger):
    def __init__(
        self,
        path: Path,
        policy: NaverUsagePolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(
            path,
            policy,
            ZoneInfo("Asia/Seoul"),
            "Invalid NAVER usage ledger",
            clock,
        )
