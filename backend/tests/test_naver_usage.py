from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.batch.naver_usage import (
    NaverPaidOverageDisabledError,
    NaverUsageLedger,
    NaverUsageLimitExceededError,
    NaverUsagePolicy,
)


def test_naver_usage_policy_allows_request_below_both_limits() -> None:
    NaverUsagePolicy().ensure_request_allowed(daily_usage=299, monthly_usage=8_999)


@pytest.mark.parametrize(
    ("daily_usage", "monthly_usage"),
    [(300, 100), (10, 9_000)],
)
def test_naver_usage_policy_stops_at_daily_or_monthly_limit(
    daily_usage: int, monthly_usage: int
) -> None:
    with pytest.raises(NaverUsageLimitExceededError):
        NaverUsagePolicy().ensure_request_allowed(
            daily_usage=daily_usage,
            monthly_usage=monthly_usage,
        )


def test_naver_usage_policy_rejects_paid_overage() -> None:
    with pytest.raises(NaverPaidOverageDisabledError):
        NaverUsagePolicy(paid_overage_enabled=True).ensure_request_allowed(
            daily_usage=0,
            monthly_usage=0,
        )


def test_naver_usage_ledger_persists_and_resets_daily_count(tmp_path: Path) -> None:
    ledger_path = tmp_path / "naver-usage.json"
    first = NaverUsageLedger(
        ledger_path,
        NaverUsagePolicy(daily_limit=2),
        clock=lambda: datetime(2026, 8, 7, 10, tzinfo=ZoneInfo("Asia/Seoul")),
    )
    first.reserve_request()
    first.reserve_request()
    with pytest.raises(NaverUsageLimitExceededError):
        first.reserve_request()

    next_day = NaverUsageLedger(
        ledger_path,
        NaverUsagePolicy(daily_limit=2),
        clock=lambda: datetime(2026, 8, 8, 10, tzinfo=ZoneInfo("Asia/Seoul")),
    )
    next_day.reserve_request()
