import html
import re
import unicodedata
from collections import Counter, OrderedDict, deque
from datetime import timedelta
from difflib import SequenceMatcher
from hashlib import sha256
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


def assign_story_clusters(articles: list[CollectedArticle]) -> list[CollectedArticle]:
    clusters: list[tuple[str, CollectedArticle]] = []
    assignments: dict[str, str] = {}
    for article in sorted(
        articles,
        key=lambda item: (item.published_at.timestamp(), item.article_id),
    ):
        cluster_id = next(
            (
                existing_id
                for existing_id, representative in clusters
                if _is_same_story(representative, article)
            ),
            None,
        )
        if cluster_id is None:
            seed = (
                f"{article.country.value}:{_canonical_headline(article.title)}:{article.article_id}"
            )
            cluster_id = sha256(seed.encode()).hexdigest()[:24]
            clusters.append((cluster_id, article))
        assignments[article.article_id] = cluster_id
    return [
        article.model_copy(update={"story_cluster_id": assignments[article.article_id]})
        for article in articles
    ]


def select_diverse_articles(articles: list[CollectedArticle], limit: int) -> list[CollectedArticle]:
    if not articles or limit <= 0:
        return []
    buckets: OrderedDict[str, deque[CollectedArticle]] = OrderedDict()
    for article in articles:
        buckets.setdefault(canonical_publisher(article.publisher), deque()).append(article)
    selected: list[CollectedArticle] = []
    while buckets and len(selected) < limit:
        exhausted: list[str] = []
        for publisher, bucket in buckets.items():
            selected.append(bucket.popleft())
            if not bucket:
                exhausted.append(publisher)
            if len(selected) >= limit:
                break
        for publisher in exhausted:
            del buckets[publisher]

    counts = Counter(canonical_publisher(article.publisher) for article in selected)
    publisher_budget = max(
        1,
        min(MAX_PUBLISHER_ARTICLES, int(len(selected) * MAX_PUBLISHER_SHARE)),
    )
    return [
        article.model_copy(
            update={
                "ranking_weight": article.ranking_weight
                * min(1.0, publisher_budget / counts[canonical_publisher(article.publisher)])
            }
        )
        for article in selected
    ]


def canonical_publisher(value: str) -> str:
    normalized = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
    normalized = re.sub(r"[^\w]+", " ", normalized).strip()
    for family, aliases in _PUBLISHER_FAMILIES.items():
        if any(alias in normalized for alias in aliases):
            return family
    return normalized


def _is_duplicate(left: CollectedArticle, right: CollectedArticle) -> bool:
    return left.url == right.url


def _is_same_story(left: CollectedArticle, right: CollectedArticle) -> bool:
    if left.country is not right.country:
        return False
    if abs(left.published_at - right.published_at) > timedelta(hours=12):
        return False
    left_title = _canonical_headline(left.title)
    right_title = _canonical_headline(right.title)
    title_similarity = SequenceMatcher(None, left_title, right_title).ratio()
    left_path = _canonical_story_path(left.url)
    right_path = _canonical_story_path(right.url)
    if left_path is not None and left_path == right_path and title_similarity >= 0.65:
        return True
    if left_title == right_title:
        return True
    if title_similarity >= 0.88:
        return True
    left_terms = set(left_title.split())
    right_terms = set(right_title.split())
    union = left_terms | right_terms
    return (
        min(len(left_terms), len(right_terms)) >= 4
        and bool(union)
        and len(left_terms & right_terms) / len(union) >= 0.8
    )


def _canonical_headline(title: str) -> str:
    text = unicodedata.normalize("NFKC", html.unescape(title)).casefold()
    return normalize_title(text)


def _canonical_story_path(url: str) -> str | None:
    path = unicodedata.normalize("NFKC", urlsplit(url).path).casefold().rstrip("/")
    if len(path) < 30 or path.count("/") < 3:
        return None
    return path


def _preferred(left: CollectedArticle, right: CollectedArticle) -> CollectedArticle:
    left_score = (bool(left.summary), len(left.summary or ""), -left.published_at.timestamp())
    right_score = (bool(right.summary), len(right.summary or ""), -right.published_at.timestamp())
    return right if right_score > left_score else left
