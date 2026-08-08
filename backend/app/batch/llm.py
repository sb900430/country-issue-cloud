import json
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from time import sleep
from typing import Protocol

from pydantic import ValidationError

from app.batch.issues import ExtractionResult
from app.batch.models import CollectedArticle
from app.schemas.issues import CountryCode


class StructuredLlmClient(Protocol):
    def complete(self, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]: ...


class CostLimitExceededError(RuntimeError):
    pass


class ExtractionFailedError(RuntimeError):
    pass


class JsonExtractionCache:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir

    def get(self, key: str) -> ExtractionResult | None:
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            return ExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, ValidationError):
            return None

    def put(self, key: str, result: ExtractionResult) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        destination = self.cache_dir / f"{key}.json"
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(destination)


class RetryingStructuredExtractor:
    def __init__(
        self,
        client: StructuredLlmClient,
        cache: JsonExtractionCache,
        model: str,
        prompt_version: str = "issues-v1",
        timeout_seconds: float = 30,
        max_retries: int = 2,
        monthly_cost_limit_usd: float = 10,
        current_month_cost_usd: Callable[[], float] = lambda: 0.0,
        retry_delay_seconds: float = 0,
    ) -> None:
        self.client = client
        self.cache = cache
        self.model = model
        self.prompt_version = prompt_version
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.monthly_cost_limit_usd = monthly_cost_limit_usd
        self.current_month_cost_usd = current_month_cost_usd
        self.retry_delay_seconds = retry_delay_seconds

    def extract(self, country: CountryCode, articles: list[CollectedArticle]) -> ExtractionResult:
        payload = self._payload(country, articles)
        cache_key = sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        if self.current_month_cost_usd() >= self.monthly_cost_limit_usd:
            raise CostLimitExceededError("monthly LLM cost limit reached")

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.complete(payload, self.timeout_seconds)
                enriched = {
                    **response,
                    "country": country,
                    "model": self.model,
                    "prompt_version": self.prompt_version,
                }
                result = ExtractionResult.model_validate(enriched)
                if self.current_month_cost_usd() + result.cost_usd > self.monthly_cost_limit_usd:
                    raise CostLimitExceededError("LLM response would exceed monthly cost limit")
                self.cache.put(cache_key, result)
                return result
            except CostLimitExceededError:
                raise
            except (OSError, RuntimeError, ValueError, ValidationError) as error:
                last_error = error
                if attempt < self.max_retries and self.retry_delay_seconds:
                    sleep(self.retry_delay_seconds)
        raise ExtractionFailedError("structured LLM extraction failed") from last_error

    def _payload(self, country: CountryCode, articles: list[CollectedArticle]) -> dict[str, object]:
        return {
            "country": country.value,
            "prompt_version": self.prompt_version,
            "articles": [
                {
                    "article_id": article.article_id,
                    "title": article.title,
                    "summary": article.summary,
                }
                for article in articles
            ],
        }
