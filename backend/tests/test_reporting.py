from pathlib import Path

from app.batch.reporting import IncidentReporter, mask_sensitive
from app.schemas.issues import CountryCode


def test_mask_sensitive_removes_common_credentials() -> None:
    masked = mask_sensitive("api_key=real-value Authorization: Bearer abc.def token=xyz")

    assert "real-value" not in masked
    assert "abc.def" not in masked
    assert "xyz" not in masked


def test_incident_report_is_local_and_contains_safe_actions(tmp_path: Path) -> None:
    path = IncidentReporter(tmp_path).write(
        "run-001",
        CountryCode.JP,
        "extract",
        RuntimeError("secret=do-not-store"),
        retries=2,
    )

    report = path.read_text(encoding="utf-8")
    assert "do-not-store" not in report
    assert "Country: JP" in report
    assert "Improvement options" in report
