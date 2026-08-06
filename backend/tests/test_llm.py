from pathlib import Path

import pytest

from app.batch.issues import ExtractedIssue
from app.batch.llm import (
    CostLimitExceededError,
    ExtractionFailedError,
    JsonExtractionCache,
    RetryingStructuredExtractor,
)
from app.schemas.issues import CountryCode
from tests.test_issues import make_article


class StubClient:
    def __init__(self, failures: int = 0, cost_usd: float = 0.01) -> None:
        self.failures = failures
        self.cost_usd = cost_usd
        self.calls = 0
        self.timeouts: list[float] = []

    def complete(self, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        self.calls += 1
        self.timeouts.append(timeout_seconds)
        if self.calls <= self.failures:
            raise RuntimeError("transient")
        article = payload["articles"][0]  # type: ignore[index]
        article_id = article["article_id"]  # type: ignore[index]
        title = article["title"]  # type: ignore[index]
        return {
            "issues": [
                ExtractedIssue(
                    issue_label=str(title),
                    display_label_ko=str(title),
                    article_ids=(str(article_id),),
                    evidence_expressions=(str(title),),
                ).model_dump(mode="json")
            ],
            "processed_article_ids": [article_id],
            "input_tokens": 10,
            "output_tokens": 5,
            "cost_usd": self.cost_usd,
        }


def test_structured_extractor_retries_and_uses_30_second_timeout(tmp_path: Path) -> None:
    client = StubClient(failures=2)
    extractor = RetryingStructuredExtractor(
        client, JsonExtractionCache(tmp_path), model="provider-model"
    )

    result = extractor.extract(CountryCode.KR, [make_article(1)])

    assert result.model == "provider-model"
    assert client.calls == 3
    assert client.timeouts == [30, 30, 30]


def test_structured_extractor_uses_content_cache(tmp_path: Path) -> None:
    client = StubClient()
    extractor = RetryingStructuredExtractor(client, JsonExtractionCache(tmp_path), model="model")
    articles = [make_article(1)]

    assert extractor.extract(CountryCode.KR, articles) == extractor.extract(
        CountryCode.KR, articles
    )
    assert client.calls == 1


def test_structured_extractor_enforces_cost_limit_before_call(tmp_path: Path) -> None:
    client = StubClient()
    extractor = RetryingStructuredExtractor(
        client,
        JsonExtractionCache(tmp_path),
        model="model",
        current_month_cost_usd=lambda: 10.0,
    )

    with pytest.raises(CostLimitExceededError):
        extractor.extract(CountryCode.KR, [make_article(1)])
    assert client.calls == 0


def test_structured_extractor_stops_after_two_retries(tmp_path: Path) -> None:
    client = StubClient(failures=3)
    extractor = RetryingStructuredExtractor(client, JsonExtractionCache(tmp_path), model="model")

    with pytest.raises(ExtractionFailedError):
        extractor.extract(CountryCode.KR, [make_article(1)])
    assert client.calls == 3
