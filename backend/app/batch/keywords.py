import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field

from app.batch.models import CollectedArticle
from app.schemas.issues import CountryCode

_NUMBER_SUFFIX = re.compile(r"\s+\d{3,}$")
_LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_KOREAN_WORD = re.compile(r"[가-힣]{2,}")
_JAPANESE_TEXT = re.compile(r"[一-龯々ぁ-んァ-ヶー]{2,}")
_ENGLISH_TAILS = {
    "affect",
    "affects",
    "change",
    "changes",
    "expand",
    "expands",
    "increase",
    "increases",
    "outlook",
    "slow",
    "slows",
}
_KOREAN_TAILS = {"감소", "둔화", "변화", "상승", "영향", "전망", "확대"}
_JAPANESE_TAILS = (
    "見通し変化",
    "見通し",
    "拡大",
    "上昇",
    "影響",
    "減速",
    "変化",
)
_GENERAL_TERMS = {
    CountryCode.US: {"economy", "market", "markets", "news", "report", "today"},
    CountryCode.JP: {"ニュース", "市場", "今日", "経済"},
    CountryCode.KR: {"경제", "기사", "뉴스", "시장", "오늘"},
}


class KeywordCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=2, max_length=80)
    evidence_expression: str = Field(min_length=2, max_length=120)


class SynonymGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    aliases: tuple[str, ...] = Field(min_length=2)


class RankedKeyword(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rank: int = Field(ge=1, le=5)
    keyword_id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=2, max_length=80)
    document_frequency: int = Field(ge=1)
    publisher_count: int = Field(ge=1)
    article_ratio: float = Field(gt=0, le=1)
    evidence_expressions: tuple[str, ...] = Field(min_length=1, max_length=10)
    related_article_ids: tuple[str, ...] = Field(min_length=1, max_length=20)


class CountryKeywordAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    country: CountryCode
    article_count: int = Field(ge=1)
    top_keywords: tuple[RankedKeyword, ...] = Field(min_length=1, max_length=5)


class LanguageKeywordExtractor:
    def extract(self, article: CollectedArticle) -> tuple[KeywordCandidate, ...]:
        title = _NUMBER_SUFFIX.sub("", article.title).strip()
        if article.country is CountryCode.US:
            label = self._english_label(title)
            evidence = label
        elif article.country is CountryCode.JP:
            label, evidence = self._japanese_label(title)
        else:
            label = self._korean_label(title)
            evidence = label
        label = label[:80].strip()
        evidence = evidence[:120].strip()
        if len(label) < 2 or len(evidence) < 2 or _normalize(label) in {
            _normalize(term) for term in _GENERAL_TERMS[article.country]
        }:
            return ()
        return (KeywordCandidate(label=label, evidence_expression=evidence),)

    @staticmethod
    def _english_label(title: str) -> str:
        words = [word.casefold() for word in _LATIN_WORD.findall(title)]
        content: list[str] = []
        for word in words:
            if word in _ENGLISH_TAILS:
                break
            if word not in _GENERAL_TERMS[CountryCode.US]:
                content.append(word)
            if len(content) == 3:
                break
        return " ".join(content)

    @staticmethod
    def _korean_label(title: str) -> str:
        words = _KOREAN_WORD.findall(title)
        content: list[str] = []
        for word in words:
            if word in _KOREAN_TAILS:
                break
            if word not in _GENERAL_TERMS[CountryCode.KR]:
                content.append(word)
            if len(content) == 3:
                break
        return " ".join(content)

    @staticmethod
    def _japanese_label(title: str) -> tuple[str, str]:
        match = _JAPANESE_TEXT.search(title)
        if match is None:
            return "", ""
        value = match.group()
        for particle in ("が", "を", "に", "へ", "で", "と", "は", "も"):
            value = value.split(particle, 1)[0]
        for tail in _JAPANESE_TAILS:
            if value.endswith(tail):
                value = value[: -len(tail)]
                break
        evidence = value.strip()
        return evidence.replace("の", "").strip(), evidence


class CandidateSynonymResolver:
    def __init__(self, groups: tuple[SynonymGroup, ...] = ()) -> None:
        self.groups = groups

    def group_key(self, label: str) -> str:
        normalized = _normalize(label)
        for index, group in enumerate(self.groups):
            if normalized in {_normalize(alias) for alias in group.aliases}:
                return f"group:{index}"
        return f"label:{normalized}"

    def display_label(self, labels: set[str]) -> str:
        normalized_labels = {_normalize(label): label for label in labels}
        for group in self.groups:
            for alias in group.aliases:
                if _normalize(alias) in normalized_labels:
                    return normalized_labels[_normalize(alias)]
        return min(labels, key=lambda value: (len(value), _normalize(value)))


class KeywordRanker:
    def __init__(
        self,
        extractor: LanguageKeywordExtractor | None = None,
        resolver: CandidateSynonymResolver | None = None,
    ) -> None:
        self.extractor = extractor or LanguageKeywordExtractor()
        self.resolver = resolver or CandidateSynonymResolver()

    def analyze(
        self, country: CountryCode, articles: list[CollectedArticle]
    ) -> CountryKeywordAnalysis:
        if len(articles) < 100:
            raise ValueError("keyword analysis requires at least 100 articles")
        if any(article.country is not country for article in articles):
            raise ValueError("keyword analysis cannot mix countries")

        grouped_articles: dict[str, dict[str, CollectedArticle]] = defaultdict(dict)
        grouped_labels: dict[str, set[str]] = defaultdict(set)
        grouped_evidence: dict[str, set[str]] = defaultdict(set)
        for article in articles:
            seen_in_article: set[str] = set()
            for candidate in self.extractor.extract(article):
                key = self.resolver.group_key(candidate.label)
                if key in seen_in_article:
                    continue
                seen_in_article.add(key)
                grouped_articles[key][article.article_id] = article
                grouped_labels[key].add(candidate.label)
                grouped_evidence[key].add(candidate.evidence_expression)

        ranked: list[tuple[int, int, datetime, str, str]] = []
        for key, indexed in grouped_articles.items():
            label = self.resolver.display_label(grouped_labels[key])
            ranked.append(
                (
                    len(indexed),
                    len({article.publisher for article in indexed.values()}),
                    max(article.published_at for article in indexed.values()),
                    _keyword_id(country, label),
                    key,
                )
            )
        ranked.sort(key=lambda item: (-item[0], -item[1], -item[2].timestamp(), item[3]))

        top_keywords: list[RankedKeyword] = []
        for rank, (frequency, publisher_count, _latest, keyword_id, key) in enumerate(
            ranked[:5], 1
        ):
            label = self.resolver.display_label(grouped_labels[key])
            related = sorted(
                grouped_articles[key].values(),
                key=lambda article: (-article.published_at.timestamp(), article.article_id),
            )[:20]
            top_keywords.append(
                RankedKeyword(
                    rank=rank,
                    keyword_id=keyword_id,
                    label=label,
                    document_frequency=frequency,
                    publisher_count=publisher_count,
                    article_ratio=frequency / len(articles),
                    evidence_expressions=tuple(sorted(grouped_evidence[key]))[:10],
                    related_article_ids=tuple(article.article_id for article in related),
                )
            )
        if len(top_keywords) < 5:
            raise ValueError("keyword analysis produced fewer than five candidates")
        return CountryKeywordAnalysis(
            country=country,
            article_count=len(articles),
            top_keywords=tuple(top_keywords),
        )


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _keyword_id(country: CountryCode, label: str) -> str:
    digest = sha256(f"{country.value}:{_normalize(label)}".encode()).hexdigest()[:12]
    return f"{country.value.lower()}-{digest}"
