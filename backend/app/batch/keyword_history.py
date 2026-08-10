import json
from collections.abc import Callable
from datetime import date
from urllib.parse import urlsplit

from pydantic import ValidationError

from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.keywords import KeywordResult


def restore_keyword_history(
    base_url: str,
    repository: JsonKeywordRepository,
    target_date: date,
    fetch: Callable[[str], bytes],
    retention_days: int = 7,
    include_latest: bool = False,
) -> list[date]:
    normalized_base = _validated_base_url(base_url)
    restored: list[date] = []
    if include_latest:
        try:
            latest = KeywordResult.model_validate_json(fetch(f"{normalized_base}/latest.json"))
        except (ValidationError, ValueError) as error:
            raise ValueError("Invalid public keyword history latest") from error
        if not 0 <= (target_date - latest.date).days < retention_days:
            raise ValueError("Public keyword history latest is outside retention")
        repository.save(latest)
        restored.append(latest.date)
    try:
        raw_dates = json.loads(fetch(f"{normalized_base}/dates.json"))
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("Invalid public keyword history index") from error
    if not isinstance(raw_dates, list):
        raise ValueError("Invalid public keyword history index")

    for raw_date in raw_dates:
        try:
            value = date.fromisoformat(raw_date) if isinstance(raw_date, str) else None
        except ValueError:
            continue
        if (
            value is None
            or value in restored
            or not 0 < (target_date - value).days < retention_days
        ):
            continue
        try:
            result = KeywordResult.model_validate_json(
                fetch(f"{normalized_base}/{value.isoformat()}.json")
            )
        except (ValidationError, ValueError) as error:
            raise ValueError(f"Invalid public keyword history: {value.isoformat()}") from error
        if result.date != value:
            raise ValueError(f"Mismatched public keyword history: {value.isoformat()}")
        repository.save_history(result)
        restored.append(value)
        if len(restored) == retention_days:
            break
    return restored


def _validated_base_url(value: str) -> str:
    parsed = urlsplit(value.rstrip("/"))
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Keyword history base URL must be a public HTTPS URL")
    return value.rstrip("/")
