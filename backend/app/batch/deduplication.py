import html
import re
import unicodedata
from collections import OrderedDict
from datetime import timedelta
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.batch.models import CollectedArticle

TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
MAX_PUBLISHER_ARTICLES = 30
MAX_PUBLISHER_SHARE = 0.2
_PUBLISHER_FAMILIES = {
    "press-release-wire": ("globe newswire", "pr newswire", "business wire"),
}


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(sorted(query)), "")
    )


def normalize_title(title: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(title))
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join(character if character.isalnum() else " " for character in text)
    return " ".join(text.split())


def deduplicate_articles(articles: list[CollectedArticle]) -> list[CollectedArticle]:
    selected: list[CollectedArticle] = []
    for candidate in articles:
        normalized_candidate = candidate.model_copy(update={"url": normalize_url(candidate.url)})
        duplicate_index = next(
            (
                index
                for index, current in enumerate(selected)
                if _is_duplicate(current, normalized_candidate)
            ),
            None,
        )
        if duplicate_index is None:
            selected.append(normalized_candidate)
        else:
            selected[duplicate_index] = _preferred(selected[duplicate_index], normalized_candidate)
    return selected


def select_diverse_articles(articles: list[CollectedArticle], limit: int) -> list[CollectedArticle]:
    if not articles or limit <= 0:
        return []
    buckets: OrderedDict[str, list[CollectedArticle]] = OrderedDict()
    for article in articles:
        buckets.setdefault(canonical_publisher(article.publisher), []).append(article)
    publisher_limit = _stable_publisher_limit(
        [len(bucket) for bucket in buckets.values()], min(len(articles), limit)
    )
    selected: list[CollectedArticle] = []
    for offset in range(publisher_limit):
        for bucket in buckets.values():
            if offset < len(bucket):
                selected.append(bucket[offset])
                if len(selected) >= limit:
                    return selected
    return selected


def canonical_publisher(value: str) -> str:
    normalized = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
    normalized = re.sub(r"[^\w]+", " ", normalized).strip()
    for family, aliases in _PUBLISHER_FAMILIES.items():
        if any(alias in normalized for alias in aliases):
            return family
    return normalized


def _stable_publisher_limit(counts: list[int], target: int) -> int:
    publisher_limit = max(1, min(MAX_PUBLISHER_ARTICLES, int(target * MAX_PUBLISHER_SHARE)))
    while publisher_limit > 1:
        available = min(target, sum(min(count, publisher_limit) for count in counts))
        adjusted = max(1, min(MAX_PUBLISHER_ARTICLES, int(available * MAX_PUBLISHER_SHARE)))
        if adjusted >= publisher_limit:
            break
        publisher_limit = adjusted
    return publisher_limit


def _is_duplicate(left: CollectedArticle, right: CollectedArticle) -> bool:
    if left.url == right.url:
        return True
    left_title = normalize_title(left.title)
    right_title = normalize_title(right.title)
    if left_title == right_title:
        return True
    within_six_hours = abs(left.published_at - right.published_at) <= timedelta(hours=6)
    return within_six_hours and SequenceMatcher(None, left_title, right_title).ratio() >= 0.92


def _preferred(left: CollectedArticle, right: CollectedArticle) -> CollectedArticle:
    left_score = (bool(left.summary), len(left.summary or ""), -left.published_at.timestamp())
    right_score = (bool(right.summary), len(right.summary or ""), -right.published_at.timestamp())
    return right if right_score > left_score else left
