import time
from collections.abc import Callable, Mapping
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx


class FeedFetchError(RuntimeError):
    def __init__(self, category: str) -> None:
        super().__init__(f"feed request failed:{category}")
        self.category = category


class HttpsFeedClient:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 15.0,
        max_response_bytes: int = 2_000_000,
        max_attempts: int = 2,
        retry_delay_seconds: float = 60.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.client = client or httpx.Client(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers={
                "Accept": (
                    "application/json, application/rss+xml, application/atom+xml, "
                    "application/xml, text/xml"
                ),
                "User-Agent": "country-issue-cloud/0.1 (+https://github.com/sb900430/country-issue-cloud)",
            },
        )
        self.max_response_bytes = max_response_bytes
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.sleeper = sleeper

    def fetch(self, url: str) -> bytes:
        return self.fetch_with_headers(url, {})

    def fetch_with_headers(self, url: str, headers: Mapping[str, str]) -> bytes:
        self._validate_url(url)
        last_error: httpx.HTTPError | None = None
        for attempt in range(self.max_attempts):
            try:
                response = self.client.get(
                    url,
                    headers=headers,
                    follow_redirects=not headers,
                )
                if headers and response.is_redirect:
                    raise FeedFetchError("authenticated_redirect")
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as error:
                last_error = error
                if error.response.status_code < 500 and error.response.status_code != 429:
                    raise FeedFetchError("client_error") from error
            except httpx.TransportError as error:
                last_error = error
            if attempt + 1 == self.max_attempts:
                raise FeedFetchError(self._error_category(last_error)) from last_error
            self.sleeper(self.retry_delay_seconds * (attempt + 1))
        else:
            raise FeedFetchError(self._error_category(last_error)) from last_error
        self._validate_url(str(response.url))
        if len(response.content) > self.max_response_bytes:
            raise FeedFetchError("response_too_large")
        content_type = response.headers.get("content-type", "").lower()
        if content_type and not any(
            allowed in content_type for allowed in ("json", "xml", "rss", "atom")
        ):
            raise FeedFetchError("unsupported_content_type")
        return response.content

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise FeedFetchError("invalid_url")
        hostname = parsed.hostname
        try:
            address = ip_address(hostname)
        except ValueError:
            if hostname == "localhost" or hostname.endswith(".localhost"):
                raise FeedFetchError("local_address") from None
        else:
            if not address.is_global:
                raise FeedFetchError("private_address")

    @staticmethod
    def _error_category(error: httpx.HTTPError | None) -> str:
        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                return "rate_limited"
            return "server_error"
        if isinstance(error, httpx.TimeoutException):
            return "timeout"
        return "transport_error"
