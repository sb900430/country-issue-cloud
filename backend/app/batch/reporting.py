import re
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.issues import CountryCode

SENSITIVE_PATTERNS = (
    re.compile(r"(?i)bearer\s+[a-z0-9._-]+"),
    re.compile(r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*(?:bearer\s+)?\S+"),
)


def mask_sensitive(value: str) -> str:
    masked = value
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub("[REDACTED]", masked)
    return masked


class IncidentReporter:
    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir

    def write(
        self,
        run_id: str,
        country: CountryCode | None,
        stage: str,
        error: Exception,
        retries: int,
    ) -> Path:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
        country_label = country.value if country is not None else "ALL"
        path = self.reports_dir / f"incident_{timestamp}_{stage}_{country_label}.md"
        safe_error = mask_sensitive(f"{type(error).__name__}: {error}")
        path.write_text(
            "\n".join(
                [
                    f"# Incident — {run_id}",
                    "",
                    f"- Country: {country_label}",
                    f"- Stage: {stage}",
                    f"- Category: {type(error).__name__}",
                    f"- Retries: {retries}",
                    "- Impact: The failed scope was isolated; the publication gate remains active.",
                    f"- Error: `{safe_error}`",
                    "",
                    "## Improvement options",
                    "",
                    "1. Verify the source or provider contract.",
                    "2. Add a sanitized regression fixture for this failure.",
                    "3. Re-run with dry-run before the next publication.",
                ]
            ),
            encoding="utf-8",
        )
        return path
