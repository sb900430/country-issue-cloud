import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Protocol
from zoneinfo import ZoneInfo


class UsagePolicy(Protocol):
    def ensure_request_allowed(self, *, daily_usage: int, monthly_usage: int) -> None: ...


class JsonUsageLedger:
    def __init__(
        self,
        path: Path,
        policy: UsagePolicy,
        timezone: ZoneInfo,
        invalid_message: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = path
        self.policy = policy
        self.timezone = timezone
        self.invalid_message = invalid_message
        self.clock = clock or (lambda: datetime.now(timezone))
        self._lock = Lock()

    def reserve_request(self) -> None:
        with self._lock:
            now = self.clock().astimezone(self.timezone)
            day_key = now.date().isoformat()
            month_key = day_key[:7]
            state = self._load()
            daily_usage = state.get("daily_usage", 0) if state.get("day") == day_key else 0
            monthly_usage = state.get("monthly_usage", 0) if state.get("month") == month_key else 0
            if not isinstance(daily_usage, int) or not isinstance(monthly_usage, int):
                raise ValueError(self.invalid_message)
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
            raise ValueError(self.invalid_message) from error
        if not isinstance(value, dict):
            raise ValueError(self.invalid_message)
        return value

    def _save(self, state: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
