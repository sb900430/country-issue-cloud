import json
from datetime import datetime
from pathlib import Path

from pydantic import TypeAdapter

from app.batch.models import CollectedArticle, CollectorKind
from app.schemas.issues import CountryCode


class FixtureCollector:
    kind = CollectorKind.FIXTURE

    def __init__(self, source_id: str, country: CountryCode, path: Path) -> None:
        self.source_id = source_id
        self.country = country
        self.path = path

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        articles = TypeAdapter(list[CollectedArticle]).validate_python(payload)
        return [
            article
            for article in articles
            if article.country == self.country
            and window_start <= article.published_at <= window_end
        ][:limit]
