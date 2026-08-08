import html
import json
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from urllib.parse import urlencode, urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.batch.models import CollectedArticle, CollectorKind
from app.batch.naver_usage import NaverPaidOverageDisabledError, NaverUsageLedger
from app.schemas.issues import CountryCode

NAVER_MAX_RESULTS_PER_REQUEST = 100
NAVER_MAX_RESULTS_TOTAL = 250
_HTML_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class NaverSource:
    source_id: str
    endpoint: str
    queries: tuple[str, ...]
    query_version: str
    allowed_domains: tuple[str, ...]
    free_policy_review_due_at: date

    def __post_init__(self) -> None:
        if self.endpoint != "https://naverapihub.apigw.ntruss.com/search/v1/news":
            raise ValueError("NAVER endpoint is not approved")
        if not self.queries or not self.allowed_domains:
            raise ValueError("NAVER source requires queries and allowed domains")


class NaverArticle(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=1_000)
    originallink: str = Field(min_length=1, max_length=2_048)
    pubDate: str = Field(min_length=1, max_length=100)


class NaverResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    items: tuple[dict[str, object], ...]


class NaverCollector:
    kind = CollectorKind.LIVE
    country = CountryCode.KR

    def __init__(
        self,
        source: NaverSource,
        fetch: Callable[[str, Mapping[str, str]], bytes],
        client_id: str,
        client_secret: str,
        usage_ledger: NaverUsageLedger,
        today: Callable[[], date] = date.today,
    ) -> None:
        if not client_id or not client_secret:
            raise ValueError("NAVER credentials are required")
        self.source = source
        self.source_id = source.source_id
        self.fetch = fetch
        self.headers = {
            "X-NCP-APIGW-API-KEY-ID": client_id,
            "X-NCP-APIGW-API-KEY": client_secret,
        }
        self.usage_ledger = usage_ledger
        self.today = today
        self.last_diagnostics: dict[str, int] = {}
        self.last_rejected_domain_counts: dict[str, int] = {}

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]:
        if self.today() > self.source.free_policy_review_due_at:
            raise NaverPaidOverageDisabledError(
                "NAVER free policy review is required before further requests"
            )
        target_limit = min(max(limit, 1), NAVER_MAX_RESULTS_TOTAL)
        self.last_diagnostics = {
            "response_items": 0,
            "domain_rejected": 0,
            "duplicate_rejected": 0,
            "date_rejected": 0,
            "title_rejected": 0,
            "limit_rejected": 0,
            "accepted": 0,
        }
        rejected_domains: Counter[str] = Counter()
        articles: list[CollectedArticle] = []
        seen_urls: set[str] = set()
        for query in self.source.queries:
            self.usage_ledger.reserve_request()
            payload = self.fetch(self._request_url(query), self.headers)
            response = self._parse_response(payload)
            self.last_diagnostics["response_items"] += len(response)
            for index, item in enumerate(response):
                domain = self._approved_domain(item.originallink)
                if domain is None:
                    self.last_diagnostics["domain_rejected"] += 1
                    rejected_domains[self._response_domain(item.originallink)] += 1
                    continue
                if item.originallink in seen_urls:
                    self.last_diagnostics["duplicate_rejected"] += 1
                    continue
                try:
                    published_at = parsedate_to_datetime(item.pubDate)
                except (TypeError, ValueError):
                    self.last_diagnostics["date_rejected"] += 1
                    continue
                if published_at.tzinfo is None or not window_start <= published_at <= window_end:
                    self.last_diagnostics["date_rejected"] += 1
                    continue
                title = self._plain_text(item.title)
                if not title:
                    self.last_diagnostics["title_rejected"] += 1
                    continue
                seen_urls.add(item.originallink)
                article_id = sha256(f"{self.source_id}:{item.originallink}".encode()).hexdigest()[
                    :24
                ]
                articles.append(
                    CollectedArticle(
                        article_id=article_id,
                        country=self.country,
                        title=title,
                        url=item.originallink,
                        publisher=domain,
                        published_at=published_at,
                    )
                )
                self.last_diagnostics["accepted"] += 1
                if len(articles) >= target_limit:
                    self.last_diagnostics["limit_rejected"] += len(response) - index - 1
                    self._store_rejected_domains(rejected_domains)
                    return articles
        self._store_rejected_domains(rejected_domains)
        return articles

    def _request_url(self, query: str) -> str:
        parameters = urlencode(
            {
                "query": query,
                "display": NAVER_MAX_RESULTS_PER_REQUEST,
                "start": 1,
                "sort": "date",
                "format": "json",
            }
        )
        return f"{self.source.endpoint}?{parameters}"

    @staticmethod
    def _parse_response(payload: bytes) -> tuple[NaverArticle, ...]:
        try:
            response = NaverResponse.model_validate(json.loads(payload))
        except (json.JSONDecodeError, TypeError, ValidationError) as error:
            raise ValueError("Invalid NAVER response") from error
        items: list[NaverArticle] = []
        for raw in response.items:
            try:
                items.append(NaverArticle.model_validate(raw))
            except ValidationError:
                continue
        return tuple(items)

    def _approved_domain(self, url: str) -> str | None:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            return None
        domain = parsed.hostname.lower().removeprefix("www.")
        return next(
            (
                allowed
                for allowed in sorted(self.source.allowed_domains, key=len, reverse=True)
                if domain == allowed or domain.endswith(f".{allowed}")
            ),
            None,
        )

    @staticmethod
    def _response_domain(url: str) -> str:
        return (urlsplit(url).hostname or "invalid").lower().removeprefix("www.")

    def _store_rejected_domains(self, counts: Counter[str]) -> None:
        self.last_rejected_domain_counts = dict(
            sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]
        )

    @staticmethod
    def _plain_text(value: str) -> str:
        return " ".join(html.unescape(_HTML_TAG.sub("", value)).split())
