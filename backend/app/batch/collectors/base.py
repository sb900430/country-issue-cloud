from datetime import datetime
from typing import Protocol

from app.batch.models import CollectedArticle, CollectorKind
from app.schemas.issues import CountryCode


class Collector(Protocol):
    source_id: str
    country: CountryCode
    kind: CollectorKind

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]: ...
