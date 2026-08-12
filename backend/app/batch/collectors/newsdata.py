import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from urllib.parse import urlencode, urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.batch.models import CollectedArticle, CollectorKind
from app.batch.newsdata_usage import NewsDataUsageLedger
from app.schemas.issues import CountryCode

NEWSDATA_ENDPOINT = "https://newsdata.io/api/1/latest"
NEWSDATA_FREE_PAGE_SIZE = 10
NEWSDATA_MAX_RESULTS_TOTAL = 150


@dataclass(frozen=True)
class NewsDataSource:
    source_id: str
    country: CountryCode
    endpoint: str
    api_country: str
    language: str
    category: str
    query_version: str
    free_policy_review_due_at: date
    blocked_publishers: tuple[str, ...] = ()
    required_title_terms: tuple[str, ...] = ()
    excluded_domains: tuple[str, ...] = ()
    availability_delay_hours: int = 0
    max_pages_per_collection: int = 20

    def __post_init__(self) -> None:
        if self.endpoint != NEWSDATA_ENDPOINT:
            raise ValueError("NewsData endpoint is not approved")
        if self.country not in {CountryCode.US, CountryCode.JP}:
            raise ValueError("NewsData supplement is limited to US and JP")
        if self.category != "business":
            raise ValueError("NewsData source must remain scoped to business news")
        if not 0 <= self.availability_delay_hours <= 48:
            raise ValueError("NewsData availability delay must be between 0 and 48 hours")
        if not 1 <= self.max_pages_per_collection <= 40:
            raise ValueError("NewsData page limit must be between 1 and 40")
        if len(self.excluded_domains) > 5:
            raise ValueError("NewsData supports at most five excluded domains")


class NewsDataArticle(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)

    article_id: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=1, max_length=1_000)
    link: str = Field(min_length=1, max_length=2_048)
    pubDate: str = Field(min_length=1, max_length=100)
    source_name: str | None = Field(default=None, max_length=200)
    source_id: str | None = Field(default=None, max_length=200)


class NewsDataResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    status: str
    results: tuple[dict[str, object], ...] = ()
    nextPage: str | None = None


class NewsDataCollector:
    kind = CollectorKind.LIVE

    def __init__(
        self,
        source: NewsDataSource,
        fetch: Callable[[str, Mapping[str, str]], bytes],
        api_key: str,
        usage_ledger: NewsDataUsageLedger,
        today: Callable[[], date] = date.today,
    ) -> None:
        if not api_key:
            raise ValueError("NewsData API key is required")
        self.source = source
        self.source_id = source.source_id
        self.country = source.country
        self.fetch = fetch
        self.api_key = api_key
        self.usage_ledger = usage_ledger
        self.today = today
        self.last_diagnostics: dict[str, int] = {}

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]:
        if self.today() > self.source.free_policy_review_due_at:
            raise ValueError("NewsData free policy review is required before further requests")
        target_limit = min(max(limit, 1), NEWSDATA_MAX_RESULTS_TOTAL)
        self.last_diagnostics = {
            "response_items": 0,
            "url_rejected": 0,
            "duplicate_rejected": 0,
            "date_rejected": 0,
            "title_rejected": 0,
            "publisher_rejected": 0,
            "relevance_rejected": 0,
            "limit_rejected": 0,
            "accepted": 0,
            "availability_delay_hours": self.source.availability_delay_hours,
        }
        effective_window_start = window_start - timedelta(
            hours=self.source.availability_delay_hours
        )
        effective_window_end = window_end - timedelta(
            hours=self.source.availability_delay_hours
        )
        articles: list[CollectedArticle] = []
        seen_urls: set[str] = set()
        page: str | None = None
        request_count = 0
        while (
            len(articles) < target_limit
            and request_count < self.source.max_pages_per_collection
        ):
            self.usage_ledger.reserve_request()
            request_count += 1
            response = self._parse_response(
                self.fetch(self._request_url(page), {"Accept": "application/json"})
            )
            self.last_diagnostics["response_items"] += len(response.results)
            for index, item in enumerate(response.results):
                if not self._is_public_https(item.link):
                    self.last_diagnostics["url_rejected"] += 1
                    continue
                if item.link in seen_urls:
                    self.last_diagnostics["duplicate_rejected"] += 1
                    continue
                published_at = self._parse_datetime(item.pubDate)
                if (
                    published_at is None
                    or not effective_window_start <= published_at <= effective_window_end
                ):
                    self.last_diagnostics["date_rejected"] += 1
                    continue
                title = " ".join(item.title.split())
                if not title:
                    self.last_diagnostics["title_rejected"] += 1
                    continue
                publisher = item.source_name or item.source_id or self._domain(item.link)
                if publisher.casefold().strip() in {
                    value.casefold().strip() for value in self.source.blocked_publishers
                }:
                    self.last_diagnostics["publisher_rejected"] += 1
                    continue
                if self.source.required_title_terms and not any(
                    term.casefold() in title.casefold()
                    for term in self.source.required_title_terms
                ):
                    self.last_diagnostics["relevance_rejected"] += 1
                    continue
                seen_urls.add(item.link)
                stable_id = item.article_id or item.link
                article_id = sha256(f"{self.source_id}:{stable_id}".encode()).hexdigest()[:24]
                articles.append(
                    CollectedArticle(
                        article_id=article_id,
                        country=self.country,
                        title=title,
                        url=item.link,
                        publisher=publisher[:200],
                        published_at=published_at,
                    )
                )
                self.last_diagnostics["accepted"] += 1
                if len(articles) >= target_limit:
                    self.last_diagnostics["limit_rejected"] += len(response.results) - index - 1
                    return articles
            if not response.nextPage or not response.results or response.nextPage == page:
                break
            page = response.nextPage
        return articles

    def _request_url(self, page: str | None) -> str:
        parameters = {
            "apikey": self.api_key,
            "country": self.source.api_country,
            "language": self.source.language,
            "category": self.source.category,
            "size": NEWSDATA_FREE_PAGE_SIZE,
            "removeduplicate": 1,
        }
        if self.source.excluded_domains:
            parameters["excludedomain"] = ",".join(self.source.excluded_domains)
        if page:
            parameters["page"] = page
        return f"{self.source.endpoint}?{urlencode(parameters)}"

    @staticmethod
    def _parse_response(payload: bytes) -> "ParsedNewsDataResponse":
        try:
            response = NewsDataResponse.model_validate(json.loads(payload))
        except (json.JSONDecodeError, TypeError, ValidationError) as error:
            raise ValueError("Invalid NewsData response") from error
        if response.status != "success":
            raise ValueError("NewsData response did not report success")
        items: list[NewsDataArticle] = []
        for raw in response.results:
            try:
                items.append(NewsDataArticle.model_validate(raw))
            except ValidationError:
                continue
        return ParsedNewsDataResponse(tuple(items), response.nextPage)

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            try:
                parsed = datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            except ValueError:
                return None
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed

    @staticmethod
    def _is_public_https(url: str) -> bool:
        parsed = urlsplit(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username

    @staticmethod
    def _domain(url: str) -> str:
        return (urlsplit(url).hostname or "NewsData.io").lower().removeprefix("www.")


@dataclass(frozen=True)
class ParsedNewsDataResponse:
    results: tuple[NewsDataArticle, ...]
    nextPage: str | None
