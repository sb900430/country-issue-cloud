from ipaddress import ip_address
from urllib.parse import urlparse

import httpx


class FeedFetchError(RuntimeError):
    pass


class HttpsFeedClient:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 15.0,
        max_response_bytes: int = 2_000_000,
        max_attempts: int = 2,
    ) -> None:
        self.client = client or httpx.Client(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers={
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                "User-Agent": "country-issue-cloud/0.1 (+https://github.com/sb900430/country-issue-cloud)",
            },
        )
        self.max_response_bytes = max_response_bytes
        self.max_attempts = max_attempts

    def fetch(self, url: str) -> bytes:
        self._validate_url(url)
        last_error: httpx.HTTPError | None = None
        for attempt in range(self.max_attempts):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as error:
                last_error = error
                if error.response.status_code < 500 and error.response.status_code != 429:
                    raise FeedFetchError("feed request failed") from error
            except httpx.TransportError as error:
                last_error = error
            if attempt + 1 == self.max_attempts:
                raise FeedFetchError("feed request failed") from last_error
        else:
            raise FeedFetchError("feed request failed") from last_error
        self._validate_url(str(response.url))
        if len(response.content) > self.max_response_bytes:
            raise FeedFetchError("feed response is too large")
        content_type = response.headers.get("content-type", "").lower()
        if content_type and not any(
            allowed in content_type for allowed in ("xml", "rss", "atom")
        ):
            raise FeedFetchError("feed response has an unsupported content type")
        return response.content

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise FeedFetchError("feed URL must be public HTTPS")
        hostname = parsed.hostname
        try:
            address = ip_address(hostname)
        except ValueError:
            if hostname == "localhost" or hostname.endswith(".localhost"):
                raise FeedFetchError("local feed URL is not allowed") from None
        else:
            if not address.is_global:
                raise FeedFetchError("private feed address is not allowed")
