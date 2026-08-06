from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree

from app.batch.models import CollectedArticle, CollectorKind
from app.schemas.issues import CountryCode


@dataclass(frozen=True)
class RssSource:
    source_id: str
    country: CountryCode
    publisher: str
    feed_url: str
    include_summary: bool = True
    ranking_weight: float = 1.0

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
        for title, url, summary, raw_published_at in self._entries(root):
            if not title or not url or not raw_published_at:
                continue
            url = self._https_url(url)
            try:
                published_at = self._parse_datetime(raw_published_at)
            except (TypeError, ValueError):
                continue
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
                    summary=(summary or None) if self.source.include_summary else None,
                    url=url,
                    publisher=self.source.publisher,
                    published_at=published_at,
                    ranking_weight=self.source.ranking_weight,
                )
            )
            if len(articles) >= limit:
                break
        return articles

    @staticmethod
    def _entries(root: ElementTree.Element) -> list[tuple[str, str, str, str]]:
        rss_items = root.findall("./channel/item")
        if rss_items:
            return [
                (
                    (item.findtext("title") or "").strip(),
                    (item.findtext("link") or "").strip(),
                    (item.findtext("description") or "").strip(),
                    (
                        item.findtext("pubDate")
                        or item.findtext("{http://purl.org/dc/elements/1.1/}date")
                        or ""
                    ).strip(),
                )
                for item in rss_items
            ]
        namespace = "{http://www.w3.org/2005/Atom}"
        return [
            (
                (entry.findtext(f"{namespace}title") or "").strip(),
                RssCollector._atom_link(entry, namespace),
                (
                    entry.findtext(f"{namespace}summary")
                    or entry.findtext(f"{namespace}content")
                    or ""
                ).strip(),
                (
                    entry.findtext(f"{namespace}published")
                    or entry.findtext(f"{namespace}updated")
                    or ""
                ).strip(),
            )
            for entry in root.findall(f"{namespace}entry")
        ]

    @staticmethod
    def _atom_link(entry: ElementTree.Element, namespace: str) -> str:
        links = entry.findall(f"{namespace}link")
        alternate = next(
            (link for link in links if link.attrib.get("rel", "alternate") == "alternate"),
            None,
        )
        selected = alternate if alternate is not None else (links[0] if links else None)
        return selected.attrib.get("href", "") if selected is not None else ""

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if len(value) == 14 and value.isdigit():
            return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _https_url(value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme == "http":
            return urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, parsed.fragment))
        return value
