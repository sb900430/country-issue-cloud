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
    with pytest.raises(FeedFetchError, match="feed URL|feed address"):
        HttpsFeedClient().fetch(url)


def test_https_feed_client_rejects_non_xml_and_oversized_responses() -> None:
    non_xml = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, headers={"content-type": "text/html"}, content=b"html"
            )
        )
    )
    with pytest.raises(FeedFetchError, match="content type"):
        HttpsFeedClient(client=non_xml).fetch("https://example.com/feed")

    oversized = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, headers={"content-type": "application/xml"}, content=b"x" * 11
            )
        )
    )
    with pytest.raises(FeedFetchError, match="too large"):
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

    assert HttpsFeedClient(client=client).fetch("https://example.com/feed") == b"<rss/>"
    assert attempts == 2
