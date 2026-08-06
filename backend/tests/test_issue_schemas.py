import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.issues import IssueResult

SAMPLE_FIXTURE = Path(__file__).parents[2] / "sample-data" / "fixtures" / "issues_2026-08-03.json"


def load_sample_payload() -> dict[str, object]:
    return json.loads(SAMPLE_FIXTURE.read_text(encoding="utf-8"))


def test_issue_result_accepts_the_three_country_contract() -> None:
    result = IssueResult.model_validate(load_sample_payload())

    assert result.date.isoformat() == "2026-08-03"
    assert result.generated_at.utcoffset() is not None
    assert len(result.countries) == 3


def test_issue_result_rejects_a_missing_country() -> None:
    payload = load_sample_payload()
    countries = payload["countries"]
    assert isinstance(countries, dict)
    countries.pop("JP")

    with pytest.raises(ValidationError, match="countries must contain exactly"):
        IssueResult.model_validate(payload)


def test_issue_result_rejects_unknown_fields() -> None:
    payload = load_sample_payload()
    payload["secret_debug_value"] = "must-not-pass"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        IssueResult.model_validate(payload)


def test_issue_result_rejects_naive_generated_time() -> None:
    payload = load_sample_payload()
    payload["generated_at"] = "2026-08-03T08:10:00"

    with pytest.raises(ValidationError, match="timezone"):
        IssueResult.model_validate(payload)
