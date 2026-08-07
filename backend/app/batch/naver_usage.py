import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from zoneinfo import ZoneInfo


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


class NaverUsageLedger:
    def __init__(
        self,
        path: Path,
        policy: NaverUsagePolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = path
        self.policy = policy
        self.clock = clock or (lambda: datetime.now(ZoneInfo("Asia/Seoul")))
        self._lock = Lock()

    def reserve_request(self) -> None:
        with self._lock:
            now = self.clock().astimezone(ZoneInfo("Asia/Seoul"))
            day_key = now.date().isoformat()
            month_key = day_key[:7]
            state = self._load()
            daily_usage = state.get("daily_usage", 0) if state.get("day") == day_key else 0
            monthly_usage = (
                state.get("monthly_usage", 0) if state.get("month") == month_key else 0
            )
            if not isinstance(daily_usage, int) or not isinstance(monthly_usage, int):
                raise ValueError("Invalid NAVER usage ledger")
            self.policy.ensure_request_allowed(
                daily_usage=daily_usage,
                monthly_usage=monthly_usage,
            )
            self._save(
                {
                    "day": day_key,
                    "daily_usage": daily_usage + 1,
                    "month": month_key,
                    "monthly_usage": monthly_usage + 1,
                }
            )

    def _load(self) -> dict[str, object]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("Invalid NAVER usage ledger") from error
        if not isinstance(value, dict):
            raise ValueError("Invalid NAVER usage ledger")
        return value

    def _save(self, state: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
