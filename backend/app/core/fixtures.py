from pathlib import Path

from pydantic import ValidationError

from app.schemas.issues import IssueResult


def load_issue_fixture(path: Path) -> IssueResult:
    try:
        return IssueResult.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as error:
        raise ValueError(f"Invalid issue fixture: {path.name}") from error
