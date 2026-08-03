import json
from pathlib import Path
from typing import Any

REQUIRED_ROOT_FIELDS = frozenset({"schema_version", "date", "generated_at", "status", "countries"})
SUPPORTED_COUNTRIES = frozenset({"US", "JP", "KR"})


def load_issue_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Fixture root must be an object")

    missing_fields = REQUIRED_ROOT_FIELDS.difference(payload)
    if missing_fields:
        raise ValueError(f"Fixture is missing required fields: {sorted(missing_fields)}")

    countries = payload["countries"]
    if not isinstance(countries, dict) or set(countries) != SUPPORTED_COUNTRIES:
        raise ValueError("Fixture countries must contain exactly US, JP, and KR")

    return payload
