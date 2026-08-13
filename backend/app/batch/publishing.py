from pathlib import Path

from app.batch.static_publishing import publish_static_history
from app.schemas.issues import IssueResult


class StaticJsonPublisher:
    def __init__(self, published_dir: Path, site_data_dir: Path) -> None:
        self.published_dir = published_dir
        self.site_data_dir = site_data_dir

    def publish(self) -> list[Path]:
        return publish_static_history(
            self.published_dir,
            self.site_data_dir,
            "issues_????-??-??.json",
            self._validate,
            "latest result has no matching dated result",
        )

    @staticmethod
    def _validate(path: Path) -> IssueResult:
        return IssueResult.model_validate_json(path.read_text(encoding="utf-8"))
