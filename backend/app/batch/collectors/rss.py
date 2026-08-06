from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from xml.etree import ElementTree

from app.batch.models import CollectedArticle, CollectorKind
from app.schemas.issues import CountryCode


@dataclass(frozen=True)
class RssSource:
    source_id: str
    country: CountryCode
    publisher: str
    feed_url: str

    def __post_init__(self) -> None:
        if not self.feed_url.startswith("https://"):
            raise ValueError("RSS feed URL must use HTTPS")


class RssCollector:
    kind = CollectorKind.LIVE

    def __init__(self, source: RssSource, fetch: Callable[[str], bytes]) -> None:
        self.source = source
        self.source_id = source.source_id
        self.country = source.country
        self.fetch = fetch

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]:
        root = ElementTree.fromstring(self.fetch(self.source.feed_url))
        articles: list[CollectedArticle] = []
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()
            raw_published_at = (item.findtext("pubDate") or "").strip()
            if not title or not url or not raw_published_at:
                continue
            published_at = parsedate_to_datetime(raw_published_at)
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)
            if not window_start <= published_at <= window_end:
                continue
            article_id = sha256(f"{self.source_id}:{url}".encode()).hexdigest()[:24]
            articles.append(
                CollectedArticle(
                    article_id=article_id,
                    country=self.country,
                    title=title,
                    summary=(item.findtext("description") or "").strip() or None,
                    url=url,
                    publisher=self.source.publisher,
                    published_at=published_at,
                )
            )
            if len(articles) >= limit:
                break
        return articles
