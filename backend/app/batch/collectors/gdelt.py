import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from threading import Lock
from urllib.parse import urlencode, urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.batch.http_client import FeedFetchError
from app.batch.models import CollectedArticle, CollectorKind
from app.schemas.issues import CountryCode

GDELT_MAX_RECORDS = 250


class GdeltFetchCircuitBreaker:
    def __init__(self, fetch: Callable[[str], bytes]) -> None:
        self.fetch = fetch
        self._lock = Lock()
        self._rate_limited = False

    def __call__(self, url: str) -> bytes:
        with self._lock:
            if self._rate_limited:
                raise FeedFetchError("circuit_open_rate_limited")
            try:
                return self.fetch(url)
            except FeedFetchError as error:
                if error.category == "rate_limited":
                    self._rate_limited = True
                raise


class RequestIntervalGate:
    def __init__(
        self,
        minimum_interval_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.minimum_interval_seconds = minimum_interval_seconds
        self.clock = clock
        self.sleeper = sleeper
        self._lock = Lock()
        self._last_request_at: float | None = None

    def __call__(self) -> None:
        with self._lock:
            now = self.clock()
            if self._last_request_at is not None:
                remaining = self.minimum_interval_seconds - (now - self._last_request_at)
                if remaining > 0:
                    self.sleeper(remaining)
            self._last_request_at = self.clock()


@dataclass(frozen=True)
class GdeltSource:
    source_id: str
    country: CountryCode
    endpoint: str
    query: str
    query_version: str
    source_country: str
    source_language: str
    allowed_domains: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.endpoint.startswith("https://"):
            raise ValueError("GDELT endpoint must use HTTPS")
        if not self.allowed_domains:
            raise ValueError("GDELT source must allow at least one domain")


class GdeltArticle(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)

    url: str = Field(min_length=1, max_length=2_048)
    title: str = Field(min_length=1, max_length=500)
    seendate: str
    domain: str = Field(min_length=1, max_length=200)
    language: str | None = None
    sourcecountry: str | None = None


class GdeltCollector:
    kind = CollectorKind.LIVE

    def __init__(
        self,
        source: GdeltSource,
        fetch: Callable[[str], bytes],
        request_gate: Callable[[], None] | None = None,
    ) -> None:
        self.source = source
        self.source_id = source.source_id
        self.country = source.country
        self.fetch = fetch
        self.request_gate = request_gate or (lambda: None)
        self.last_diagnostics: dict[str, int] = {}

    def collect(
        self, window_start: datetime, window_end: datetime, limit: int
    ) -> list[CollectedArticle]:
        request_limit = min(max(limit, 1), GDELT_MAX_RECORDS)
        self.request_gate()
        payload = self.fetch(self._request_url(window_start, window_end, request_limit))
        response = self._parse_response(payload)
        self.last_diagnostics = {
            "response_items": len(response),
            "scope_rejected": 0,
            "domain_rejected": 0,
            "date_rejected": 0,
            "insecure_url_rejected": 0,
            "accepted": 0,
        }
        articles: list[CollectedArticle] = []
        for item in response:
            if not self._matches_source_scope(item):
                self.last_diagnostics["scope_rejected"] += 1
                continue
            response_domain = self._approved_domain(item.domain)
            url_domain = self._approved_domain(urlsplit(item.url).hostname or "")
            if response_domain is None or response_domain != url_domain:
                self.last_diagnostics["domain_rejected"] += 1
                continue
            try:
                published_at = self._parse_datetime(item.seendate)
            except ValueError:
                self.last_diagnostics["date_rejected"] += 1
                continue
            if not window_start <= published_at <= window_end:
                self.last_diagnostics["date_rejected"] += 1
                continue
            if not item.url.startswith("https://"):
                self.last_diagnostics["insecure_url_rejected"] += 1
                continue
            article_id = sha256(f"{self.source_id}:{item.url}".encode()).hexdigest()[:24]
            articles.append(
                CollectedArticle(
                    article_id=article_id,
                    country=self.country,
                    title=item.title.strip(),
                    url=item.url,
                    publisher=response_domain,
                    published_at=published_at,
                )
            )
            self.last_diagnostics["accepted"] += 1
            if len(articles) >= request_limit:
                break
        return articles

    def _request_url(self, window_start: datetime, window_end: datetime, limit: int) -> str:
        query = " ".join(
            (
                f"({self.source.query})",
                f"sourcecountry:{self.source.source_country}",
                f"sourcelang:{self.source.source_language}",
            )
        )
        parameters = urlencode(
            {
                "query": query,
                "mode": "artlist",
                "maxrecords": limit,
                "startdatetime": self._format_datetime(window_start),
                "enddatetime": self._format_datetime(window_end),
                "sort": "datedesc",
                "format": "json",
            }
        )
        return f"{self.source.endpoint}?{parameters}"

    @staticmethod
    def _parse_response(payload: bytes) -> tuple[GdeltArticle, ...]:
        try:
            raw = json.loads(payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError("Invalid GDELT response") from error
        if not isinstance(raw, dict) or not isinstance(raw.get("articles"), list):
            raise ValueError("Invalid GDELT response")
        articles: list[GdeltArticle] = []
        for item in raw["articles"]:
            try:
                articles.append(GdeltArticle.model_validate(item))
            except ValidationError:
                continue
        return tuple(articles)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if len(value) == 16 and value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return value.astimezone(UTC).strftime("%Y%m%d%H%M%S")

    @staticmethod
    def _normalized_domain(value: str) -> str:
        candidate = value.strip().lower().removeprefix("www.")
        if "://" in candidate:
            candidate = (urlsplit(candidate).hostname or "").removeprefix("www.")
        return candidate

    def _approved_domain(self, domain: str) -> str | None:
        normalized = self._normalized_domain(domain)
        return next(
            (
                allowed
                for allowed in sorted(self.source.allowed_domains, key=len, reverse=True)
                if normalized == allowed or normalized.endswith(f".{allowed}")
            ),
            None,
        )

    def _matches_source_scope(self, item: GdeltArticle) -> bool:
        if item.language and self._normalized_label(item.language) != self._normalized_label(
            self.source.source_language
        ):
            return False
        return not item.sourcecountry or self._normalized_label(
            item.sourcecountry
        ) == self._normalized_label(self.source.source_country)

    @staticmethod
    def _normalized_label(value: str) -> str:
        return "".join(character for character in value.casefold() if character.isalnum())
