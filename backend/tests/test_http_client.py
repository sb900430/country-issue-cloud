import httpx
import pytest

from app.batch.http_client import FeedFetchError, HttpsFeedClient


def test_https_feed_client_fetches_xml_with_safe_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"].startswith("application/rss+xml")
        assert "country-issue-cloud" in request.headers["user-agent"]
        return httpx.Response(
            200,
            headers={"content-type": "application/rss+xml"},
            content=b"<rss />",
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            "User-Agent": "country-issue-cloud/0.1",
        },
    )

    assert HttpsFeedClient(client=client).fetch("https://example.com/feed.xml") == b"<rss />"


def test_https_feed_client_identifies_the_current_repository() -> None:
    feed_client = HttpsFeedClient()
    try:
        assert feed_client.client.headers["user-agent"] == (
            "country-issue-cloud/0.1 "
            "(+https://github.com/kimsb0430/country-issue-cloud)"
        )
    finally:
        feed_client.client.close()


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/feed.xml",
        "https://localhost/feed.xml",
        "https://127.0.0.1/feed.xml",
        "https://user:password@example.com/feed.xml",
    ],
)
def test_https_feed_client_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(FeedFetchError):
        HttpsFeedClient().fetch(url)


def test_https_feed_client_rejects_non_xml_and_oversized_responses() -> None:
    non_xml = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, headers={"content-type": "text/html"}, content=b"html"
            )
        )
    )
    with pytest.raises(FeedFetchError, match="unsupported_content_type"):
        HttpsFeedClient(client=non_xml).fetch("https://example.com/feed")

    oversized = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, headers={"content-type": "application/xml"}, content=b"x" * 11
            )
        )
    )
    with pytest.raises(FeedFetchError, match="response_too_large"):
        HttpsFeedClient(client=oversized, max_response_bytes=10).fetch(
            "https://example.com/feed"
        )


def test_https_feed_client_retries_one_transient_failure() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(200, headers={"content-type": "application/xml"}, content=b"<rss/>")

    client = httpx.Client(transport=httpx.MockTransport(handler))

    assert HttpsFeedClient(client=client, sleeper=lambda _: None).fetch(
        "https://example.com/feed"
    ) == b"<rss/>"
    assert attempts == 2


def test_https_feed_client_accepts_json_for_news_api() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, headers={"content-type": "application/json"}, content=b'{"articles":[]}'
            )
        )
    )

    assert HttpsFeedClient(client=client).fetch("https://example.com/news") == b'{"articles":[]}'


def test_https_feed_client_adds_per_request_authentication_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-id"] == "id"
        assert request.headers["x-api-secret"] == "secret"
        return httpx.Response(200, headers={"content-type": "application/json"}, json={})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    assert HttpsFeedClient(client=client).fetch_with_headers(
        "https://example.com/news",
        {"x-api-id": "id", "x-api-secret": "secret"},
    ) == b"{}"


def test_https_feed_client_does_not_forward_authentication_across_redirects() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(302, headers={"location": "https://attacker.example/news"})

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)

    with pytest.raises(FeedFetchError, match="authenticated_redirect"):
        HttpsFeedClient(client=client).fetch_with_headers(
            "https://example.com/news",
            {"x-api-secret": "secret"},
        )

    assert calls == 1


@pytest.mark.parametrize(
    ("status_code", "category"),
    [(429, "rate_limited"), (503, "server_error"), (403, "client_error")],
)
def test_https_feed_client_classifies_http_failures(
    status_code: int, category: str
) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(status_code))
    )

    with pytest.raises(FeedFetchError) as captured:
        HttpsFeedClient(client=client, max_attempts=1).fetch("https://example.com/feed")

    assert captured.value.category == category


def test_https_feed_client_classifies_timeout() -> None:
    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    client = httpx.Client(transport=httpx.MockTransport(timeout))

    with pytest.raises(FeedFetchError) as captured:
        HttpsFeedClient(client=client, max_attempts=1).fetch("https://example.com/feed")

    assert captured.value.category == "timeout"
