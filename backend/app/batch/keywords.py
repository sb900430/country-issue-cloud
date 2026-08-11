import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from math import ceil

from kiwipiepy import Kiwi  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field
from sudachipy import dictionary, tokenizer  # type: ignore[import-untyped]

from app.batch.keyword_blocklist import KeywordBlocklist
from app.batch.models import CollectedArticle
from app.schemas.issues import CountryCode

_NUMBER_SUFFIX = re.compile(r"\s+\d{3,}$")
_LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_MIN_DOCUMENT_RATIO = 0.05
_MIN_DOCUMENT_FREQUENCY = 4
_MIN_PUBLISHER_COUNT = 2
_MIN_ARTICLE_COUNT = 70
_MAX_RELATED_ARTICLE_JACCARD = 0.5
_GENERAL_TERMS = {
    CountryCode.US: {
        "after",
        "amid",
        "announces",
        "affect",
        "affects",
        "business",
        "change",
        "changes",
        "demand",
        "economy",
        "earning",
        "expand",
        "expands",
        "government",
        "investment",
        "increase",
        "increases",
        "market",
        "markets",
        "average",
        "day",
        "moving",
        "news",
        "outlook",
        "policy",
        "report",
        "result",
        "says",
        "share",
        "stock",
        "price",
        "quarterly",
        "slow",
        "slows",
        "today",
    },
    CountryCode.JP: {
        "ニュース",
        "今日",
        "会見",
        "公表",
        "変化",
        "市場",
        "影響",
        "投資",
        "拡大",
        "政府",
        "政策",
        "明らか",
        "検討",
        "減速",
        "発表",
        "経済",
        "見通し",
        "速報",
        "上昇",
        "需要",
        "発売",
        "開催",
    },
    CountryCode.KR: {
        "감소",
        "경제",
        "기사",
        "뉴스",
        "대통령",
        "둔화",
        "변화",
        "보도",
        "속보",
        "수요",
        "시장",
        "상승",
        "영향",
        "오늘",
        "전망",
        "정부",
        "정책",
        "종합",
        "증가",
        "투자",
        "확대",
        "억원",
        "출시",
        "특징주",
        "호실적",
        "규모",
    },
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


@dataclass(frozen=True)
class _TermUnit:
    label: str
    start: int
    end: int


class LanguageKeywordExtractor:
    def __init__(self) -> None:
        self._kiwi = Kiwi()
        self._sudachi = dictionary.Dictionary(dict="core").create()

    def extract(self, article: CollectedArticle) -> tuple[KeywordCandidate, ...]:
        title = _NUMBER_SUFFIX.sub("", article.title).strip()
        if article.country is CountryCode.US:
            segments = self._english_segments(title)
        elif article.country is CountryCode.JP:
            segments = self._japanese_segments(title)
        else:
            segments = self._korean_segments(title)
        return self._build_candidates(article.country, title, segments)

    @staticmethod
    def _english_segments(title: str) -> list[list[_TermUnit]]:
        segments: list[list[_TermUnit]] = []
        current: list[_TermUnit] = []
        for match in _LATIN_WORD.finditer(title):
            surface = match.group().casefold()
            label = _english_lemma(surface)
            if (
                surface in _GENERAL_TERMS[CountryCode.US]
                or label in _GENERAL_TERMS[CountryCode.US]
                or len(label) < 3
            ):
                if current:
                    segments.append(current)
                    current = []
                continue
            current.append(_TermUnit(label, match.start(), match.end()))
        if current:
            segments.append(current)
        return segments

    def _korean_segments(self, title: str) -> list[list[_TermUnit]]:
        segments: list[list[_TermUnit]] = []
        current: list[_TermUnit] = []
        for token in self._kiwi.tokenize(title):
            if token.tag.startswith("N"):
                current.append(_TermUnit(token.form, token.start, token.start + token.len))
            elif token.tag == "XSN" and current:
                previous = current[-1]
                current[-1] = _TermUnit(
                    previous.label + token.form, previous.start, token.start + token.len
                )
            elif current:
                segments.append(current)
                current = []
        if current:
            segments.append(current)
        return segments

    def _japanese_segments(self, title: str) -> list[list[_TermUnit]]:
        segments: list[list[_TermUnit]] = []
        current: list[_TermUnit] = []
        mode = tokenizer.Tokenizer.SplitMode.C
        for morpheme in self._sudachi.tokenize(title, mode):
            part = morpheme.part_of_speech()[0]
            if part == "名詞":
                current.append(
                    _TermUnit(morpheme.dictionary_form(), morpheme.begin(), morpheme.end())
                )
            elif part == "接尾辞" and current:
                previous = current[-1]
                current[-1] = _TermUnit(
                    previous.label + morpheme.surface(), previous.start, morpheme.end()
                )
            elif part == "助詞" and morpheme.surface() == "の":
                continue
            elif current:
                segments.append(current)
                current = []
        if current:
            segments.append(current)
        return segments

    @staticmethod
    def _build_candidates(
        country: CountryCode, title: str, segments: list[list[_TermUnit]]
    ) -> tuple[KeywordCandidate, ...]:
        candidates: dict[str, KeywordCandidate] = {}
        general_terms = _GENERAL_TERMS[country]
        for segment in segments:
            covered: set[int] = set()
            for index, (left, right) in enumerate(zip(segment, segment[1:], strict=False)):
                if left.label in general_terms or right.label in general_terms:
                    continue
                separator = " " if country is CountryCode.US else ""
                label = f"{left.label}{separator}{right.label}"
                if len(label) > 30:
                    continue
                evidence = title[left.start : right.end].strip()
                if country is CountryCode.US:
                    evidence = evidence.casefold()
                if len(evidence) < 2 or _is_invalid_candidate(country, label):
                    continue
                normalized = _normalize(label)
                candidates[normalized] = KeywordCandidate(
                    label=label[:80], evidence_expression=evidence[:120]
                )
                covered.update((index, index + 1))
            for index, unit in enumerate(segment):
                if index in covered or unit.label in general_terms or len(unit.label) < 2:
                    continue
                label = unit.label[:80].strip()
                evidence = title[unit.start : unit.end][:120].strip()
                if country is CountryCode.US:
                    evidence = evidence.casefold()
                if (
                    len(label) < 2
                    or len(evidence) < 2
                    or _is_invalid_candidate(country, label)
                ):
                    continue
                normalized = _normalize(label)
                candidates[normalized] = KeywordCandidate(
                    label=label, evidence_expression=evidence
                )
        return tuple(candidates.values())


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
        blocklist: KeywordBlocklist | None = None,
    ) -> None:
        self.extractor = extractor or LanguageKeywordExtractor()
        self.resolver = resolver or CandidateSynonymResolver()
        self.blocklist = blocklist or KeywordBlocklist.load()

    def analyze(
        self, country: CountryCode, articles: list[CollectedArticle]
    ) -> CountryKeywordAnalysis:
        if len(articles) < _MIN_ARTICLE_COUNT:
            raise ValueError(f"keyword analysis requires at least {_MIN_ARTICLE_COUNT} articles")
        if any(article.country is not country for article in articles):
            raise ValueError("keyword analysis cannot mix countries")

        grouped_articles: dict[str, dict[str, CollectedArticle]] = defaultdict(dict)
        grouped_labels: dict[str, set[str]] = defaultdict(set)
        grouped_evidence: dict[str, set[str]] = defaultdict(set)
        for article in articles:
            seen_in_article: set[str] = set()
            for candidate in self.extractor.extract(article):
                if self.blocklist.blocks(country, candidate.label):
                    continue
                key = self.resolver.group_key(candidate.label)
                if key in seen_in_article:
                    continue
                seen_in_article.add(key)
                grouped_articles[key][article.article_id] = article
                grouped_labels[key].add(candidate.label)
                grouped_evidence[key].add(candidate.evidence_expression)

        minimum_frequency = max(
            _MIN_DOCUMENT_FREQUENCY, ceil(len(articles) * _MIN_DOCUMENT_RATIO)
        )
        ranked: list[tuple[int, int, datetime, str, str]] = []
        for key, indexed in grouped_articles.items():
            frequency = len(indexed)
            publisher_count = len({article.publisher for article in indexed.values()})
            if frequency < minimum_frequency or publisher_count < _MIN_PUBLISHER_COUNT:
                continue
            label = self.resolver.display_label(grouped_labels[key])
            ranked.append(
                (
                    frequency,
                    publisher_count,
                    max(article.published_at for article in indexed.values()),
                    _keyword_id(country, label),
                    key,
                )
            )
        ranked.sort(key=lambda item: (-item[0], -item[1], -item[2].timestamp(), item[3]))

        selected: list[tuple[int, int, datetime, str, str]] = []
        for ranked_item in ranked:
            key = ranked_item[4]
            if any(
                _related_article_jaccard(grouped_articles[key], grouped_articles[item[4]])
                >= _MAX_RELATED_ARTICLE_JACCARD
                for item in selected
            ):
                continue
            selected.append(ranked_item)
            if len(selected) == 5:
                break

        top_keywords: list[RankedKeyword] = []
        for rank, (frequency, publisher_count, _latest, keyword_id, key) in enumerate(
            selected, 1
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


def _english_lemma(value: str) -> str:
    if len(value) > 4 and value.endswith("ies"):
        return f"{value[:-3]}y"
    if len(value) > 4 and value.endswith("s") and not value.endswith(
        ("ics", "is", "ss", "us")
    ):
        return value[:-1]
    return value


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _is_invalid_candidate(country: CountryCode, label: str) -> bool:
    normalized = _normalize(label)
    if normalized in _GENERAL_TERMS[country]:
        return True
    if country is CountryCode.JP:
        if re.fullmatch(r"\d{1,4}[年月日]", normalized):
            return True
        return re.fullmatch(r"[年月日春夏秋冬]{2,}", normalized) is not None
    if country is CountryCode.KR:
        compact = normalized.replace(" ", "")
        return re.fullmatch(r"(?:억|조|만)?원(?:규모)?", compact) is not None
    return False


def _related_article_jaccard(
    left: dict[str, CollectedArticle], right: dict[str, CollectedArticle]
) -> float:
    left_ids = set(left)
    right_ids = set(right)
    union = left_ids | right_ids
    return len(left_ids & right_ids) / len(union) if union else 0.0


def _keyword_id(country: CountryCode, label: str) -> str:
    digest = sha256(f"{country.value}:{_normalize(label)}".encode()).hexdigest()[:12]
    return f"{country.value.lower()}-{digest}"
