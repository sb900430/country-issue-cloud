import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from math import ceil

import numpy as np
from kiwipiepy import Kiwi  # type: ignore[import-untyped]
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field
from sudachipy import dictionary, tokenizer  # type: ignore[import-untyped]

from app.batch.deduplication import canonical_publisher
from app.batch.keyword_blocklist import KeywordBlocklist
from app.batch.models import CollectedArticle
from app.batch.semantic_keywords import SemanticCandidateGrouper
from app.schemas.issues import CountryCode

_NUMBER_SUFFIX = re.compile(r"\s+\d{3,}$")
_LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_MIN_DOCUMENT_RATIO = 0.02
_MIN_DOCUMENT_FREQUENCY = 3
_MIN_PUBLISHER_COUNT = 2
_MIN_ARTICLE_COUNT = 50
_MAX_RELATED_ARTICLE_JACCARD = 0.5
_GENERAL_TERMS = {
    CountryCode.US: {
        "about",
        "after",
        "amid",
        "announces",
        "affect",
        "affects",
        "business",
        "billion",
        "close",
        "code",
        "company",
        "corp",
        "corporation",
        "free",
        "deal",
        "gain",
        "global",
        "how",
        "inc",
        "incorporated",
        "investor",
        "just",
        "large",
        "launch",
        "launched",
        "launches",
        "lower",
        "new",
        "off",
        "out",
        "plan",
        "project",
        "promo",
        "sale",
        "this",
        "year",
        "american",
        "holding",
        "casino",
        "call",
        "and",
        "are",
        "for",
        "from",
        "has",
        "have",
        "into",
        "its",
        "more",
        "of",
        "on",
        "or",
        "over",
        "than",
        "that",
        "the",
        "under",
        "was",
        "will",
        "with",
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
        "million",
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
        "home",
        "sell",
        "stock",
        "price",
        "quarterly",
        "slow",
        "slows",
        "today",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
        "jan",
        "feb",
        "mar",
        "apr",
        "jun",
        "jul",
        "aug",
        "sep",
        "sept",
        "oct",
        "nov",
        "dec",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    },
    CountryCode.JP: {
        "ニュース",
        "令和",
        "日本",
        "本日",
        "注目",
        "理由",
        "新聞",
        "一時",
        "月期",
        "情報",
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
        "下落",
        "急騰",
        "急落",
        "決算",
        "銘柄",
        "更新",
        "目標",
        "予想",
        "結果",
        "過去",
        "企業",
        "半年",
        "オンライン",
        "産経新聞",
        "ザイ",
        "売上高",
        "分析",
        "ny",
    },
    CountryCode.KR: {
        "감소",
        "경제",
        "기사",
        "개입",
        "개최",
        "기대",
        "국제",
        "뉴스",
        "대통령",
        "둔화",
        "변화",
        "보도",
        "속보",
        "수요",
        "시장",
        "상승",
        "상반기",
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
        "하반기",
        "급등",
        "금융",
        "규모",
        "사업",
        "최대",
        "대응",
        "논의",
        "취임",
        "평화",
        "경총",
        "서울",
        "국가",
        "규탄",
        "박람회",
        "용산",
    },
}
_GENERAL_TERMS[CountryCode.US].update(
    {
        "a",
        "all",
        "an",
        "any",
        "as",
        "at",
        "be",
        "best",
        "but",
        "by",
        "can",
        "city",
        "ceo",
        "customer",
        "data",
        "drop",
        "get",
        "got",
        "he",
        "her",
        "here",
        "his",
        "i",
        "if",
        "in",
        "is",
        "it",
        "my",
        "need",
        "no",
        "not",
        "now",
        "our",
        "public",
        "read",
        "real",
        "service",
        "see",
        "show",
        "study",
        "take",
        "their",
        "them",
        "these",
        "they",
        "those",
        "to",
        "top",
        "up",
        "we",
        "what",
        "when",
        "where",
        "who",
        "why",
        "you",
        "your",
    }
)
_GENERAL_TERMS[CountryCode.JP].add("online")
_GENERAL_TERMS[CountryCode.KR].update({"회견", "공원", "대표", "발동", "대책"})


class KeywordCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=2, max_length=80)
    evidence_expression: str = Field(min_length=2, max_length=120)
    term_count: int = Field(default=1, ge=1, le=2)


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
    top_keywords: tuple[RankedKeyword, ...] = Field(min_length=3, max_length=5)


@dataclass(frozen=True)
class _TermUnit:
    label: str
    start: int
    end: int


@dataclass(frozen=True)
class _RankedItem:
    quality_score: float
    frequency: int
    publisher_count: int
    specificity: int
    latest: datetime
    keyword_id: str
    key: str


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
            surface = match.group().casefold().strip("'")
            if surface.endswith("'s"):
                surface = surface[:-2]
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
            for left, right in zip(segment, segment[1:], strict=False):
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
                    label=label[:80], evidence_expression=evidence[:120], term_count=2
                )
            for unit in segment:
                if unit.label in general_terms or len(unit.label) < 2:
                    continue
                label = unit.label[:80].strip()
                evidence = title[unit.start : unit.end][:120].strip()
                if country is CountryCode.US:
                    evidence = evidence.casefold()
                if len(label) < 2 or len(evidence) < 2 or _is_invalid_candidate(country, label):
                    continue
                normalized = _normalize(label)
                candidates[normalized] = KeywordCandidate(label=label, evidence_expression=evidence)
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

    def display_label(
        self,
        labels: set[str],
        document_frequencies: Mapping[str, int] | None = None,
        term_counts: Mapping[str, int] | None = None,
    ) -> str:
        normalized_labels = {_normalize(label): label for label in labels}
        for group in self.groups:
            for alias in group.aliases:
                if _normalize(alias) in normalized_labels:
                    return normalized_labels[_normalize(alias)]
        frequencies = document_frequencies or {}
        specificity = term_counts or {}
        return min(
            labels,
            key=lambda value: (
                -frequencies.get(value, 0),
                -specificity.get(value, 1),
                len(value),
                _normalize(value),
            ),
        )


class KeywordRanker:
    def __init__(
        self,
        extractor: LanguageKeywordExtractor | None = None,
        resolver: CandidateSynonymResolver | None = None,
        blocklist: KeywordBlocklist | None = None,
        semantic_grouper: SemanticCandidateGrouper | None = None,
    ) -> None:
        self.extractor = extractor or LanguageKeywordExtractor()
        self.resolver = resolver or CandidateSynonymResolver()
        self.blocklist = blocklist or KeywordBlocklist.load()
        self.semantic_grouper = semantic_grouper

    def analyze(
        self, country: CountryCode, articles: list[CollectedArticle]
    ) -> CountryKeywordAnalysis:
        if len(articles) < _MIN_ARTICLE_COUNT:
            raise ValueError(f"keyword analysis requires at least {_MIN_ARTICLE_COUNT} articles")
        if any(article.country is not country for article in articles):
            raise ValueError("keyword analysis cannot mix countries")

        grouped_articles: dict[str, dict[str, CollectedArticle]] = defaultdict(dict)
        grouped_labels: dict[str, set[str]] = defaultdict(set)
        grouped_label_articles: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        grouped_label_term_counts: dict[str, dict[str, int]] = defaultdict(dict)
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
                grouped_label_articles[key][candidate.label].add(article.article_id)
                grouped_label_term_counts[key][candidate.label] = max(
                    candidate.term_count,
                    grouped_label_term_counts[key].get(candidate.label, 1),
                )
                grouped_evidence[key].add(candidate.evidence_expression)

        if self.semantic_grouper is not None:
            eligible_keys = {
                key
                for key, indexed in grouped_articles.items()
                if len(indexed) >= 2
                and len(
                    {canonical_publisher(article.publisher) for article in indexed.values()}
                )
                >= 2
            }
            display_labels = {
                key: self.resolver.display_label(
                    labels,
                    {label: len(grouped_label_articles[key][label]) for label in labels},
                    grouped_label_term_counts[key],
                )
                for key, labels in grouped_labels.items()
                if key in eligible_keys
            }
            assignments = {key: key for key in grouped_articles}
            assignments.update(
                self.semantic_grouper.group(
                    display_labels,
                    {key: len(indexed) for key, indexed in grouped_articles.items()},
                )
            )
            (
                grouped_articles,
                grouped_labels,
                grouped_label_articles,
                grouped_label_term_counts,
                grouped_evidence,
            ) = _merge_semantic_groups(
                assignments,
                grouped_articles,
                grouped_labels,
                grouped_label_articles,
                grouped_label_term_counts,
                grouped_evidence,
            )

        title_vectors = self._title_vectors(articles)
        minimum_frequency = max(_MIN_DOCUMENT_FREQUENCY, ceil(len(articles) * _MIN_DOCUMENT_RATIO))
        ranked: list[_RankedItem] = []
        for key, indexed in grouped_articles.items():
            frequency = len(indexed)
            publisher_count = len(
                {canonical_publisher(article.publisher) for article in indexed.values()}
            )
            if frequency < minimum_frequency or publisher_count < _MIN_PUBLISHER_COUNT:
                continue
            label = self.resolver.display_label(
                grouped_labels[key],
                {value: len(grouped_label_articles[key][value]) for value in grouped_labels[key]},
                grouped_label_term_counts[key],
            )
            cohesion = _title_cohesion(indexed, title_vectors)
            ranked.append(
                _RankedItem(
                    quality_score=frequency * (0.5 + cohesion),
                    frequency=frequency,
                    publisher_count=publisher_count,
                    specificity=grouped_label_term_counts[key][label],
                    latest=max(article.published_at for article in indexed.values()),
                    keyword_id=_keyword_id(country, label),
                    key=key,
                )
            )
        ranked.sort(
            key=lambda item: (
                -item.quality_score,
                -item.frequency,
                -item.publisher_count,
                -item.specificity,
                -item.latest.timestamp(),
                item.keyword_id,
            )
        )

        selected: list[_RankedItem] = []
        for ranked_item in ranked:
            key = ranked_item.key
            if any(
                _related_article_jaccard(grouped_articles[key], grouped_articles[item.key])
                >= _MAX_RELATED_ARTICLE_JACCARD
                for item in selected
            ):
                continue
            selected.append(ranked_item)
            if len(selected) == 5:
                break

        top_keywords: list[RankedKeyword] = []
        for rank, item in enumerate(selected, 1):
            key = item.key
            label = self.resolver.display_label(
                grouped_labels[key],
                {value: len(grouped_label_articles[key][value]) for value in grouped_labels[key]},
                grouped_label_term_counts[key],
            )
            related = _central_related_articles(grouped_articles[key], title_vectors)[:20]
            top_keywords.append(
                RankedKeyword(
                    rank=rank,
                    keyword_id=item.keyword_id,
                    label=label,
                    document_frequency=item.frequency,
                    publisher_count=item.publisher_count,
                    article_ratio=item.frequency / len(articles),
                    evidence_expressions=tuple(sorted(grouped_evidence[key]))[:10],
                    related_article_ids=tuple(article.article_id for article in related),
                )
            )
        if len(top_keywords) < 3:
            raise ValueError("keyword analysis produced fewer than three candidates")
        return CountryKeywordAnalysis(
            country=country,
            article_count=len(articles),
            top_keywords=tuple(top_keywords),
        )

    def _title_vectors(
        self, articles: list[CollectedArticle]
    ) -> dict[str, NDArray[np.float32]]:
        if self.semantic_grouper is None or not self.semantic_grouper.use_title_cohesion:
            return {}
        ordered = sorted(articles, key=lambda article: article.article_id)
        vectors = self.semantic_grouper.model.encode([article.title for article in ordered])
        if vectors.ndim != 2 or vectors.shape[0] != len(ordered) or not np.isfinite(vectors).all():
            raise ValueError("embedding model returned invalid title vectors")
        return {article.article_id: vectors[index] for index, article in enumerate(ordered)}


def _merge_semantic_groups(
    assignments: Mapping[str, str],
    grouped_articles: Mapping[str, dict[str, CollectedArticle]],
    grouped_labels: Mapping[str, set[str]],
    grouped_label_articles: Mapping[str, dict[str, set[str]]],
    grouped_label_term_counts: Mapping[str, dict[str, int]],
    grouped_evidence: Mapping[str, set[str]],
) -> tuple[
    dict[str, dict[str, CollectedArticle]],
    dict[str, set[str]],
    dict[str, dict[str, set[str]]],
    dict[str, dict[str, int]],
    dict[str, set[str]],
]:
    merged_articles: dict[str, dict[str, CollectedArticle]] = defaultdict(dict)
    merged_labels: dict[str, set[str]] = defaultdict(set)
    merged_label_articles: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    merged_label_term_counts: dict[str, dict[str, int]] = defaultdict(dict)
    merged_evidence: dict[str, set[str]] = defaultdict(set)
    for source_key, target_key in assignments.items():
        merged_articles[target_key].update(grouped_articles[source_key])
        merged_labels[target_key].update(grouped_labels[source_key])
        for label, article_ids in grouped_label_articles[source_key].items():
            merged_label_articles[target_key][label].update(article_ids)
            merged_label_term_counts[target_key][label] = max(
                grouped_label_term_counts[source_key][label],
                merged_label_term_counts[target_key].get(label, 1),
            )
        merged_evidence[target_key].update(grouped_evidence[source_key])
    return (
        dict(merged_articles),
        dict(merged_labels),
        {key: dict(values) for key, values in merged_label_articles.items()},
        dict(merged_label_term_counts),
        dict(merged_evidence),
    )


def _english_lemma(value: str) -> str:
    if len(value) > 4 and value.endswith("ies"):
        return f"{value[:-3]}y"
    if len(value) > 5 and value.endswith(("ches", "shes", "sses", "xes", "zes", "oes")):
        return value[:-2]
    if len(value) > 4 and value.endswith("s") and not value.endswith(("ics", "is", "ss", "us")):
        return value[:-1]
    return value


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _is_invalid_candidate(country: CountryCode, label: str) -> bool:
    normalized = _normalize(label)
    if normalized in _GENERAL_TERMS[country]:
        return True
    if country is CountryCode.JP:
        if re.fullmatch(r"[\d.,]+", normalized):
            return True
        if any(character.isdigit() for character in normalized) and any(
            marker in normalized for marker in "年月日"
        ):
            return True
        return re.fullmatch(r"[年月日春夏秋冬]{2,}", normalized) is not None
    if country is CountryCode.KR:
        compact = normalized.replace(" ", "")
        return re.fullmatch(r"(?:억|조|만)?원(?:규모)?", compact) is not None
    return False


def _title_cohesion(
    articles: Mapping[str, CollectedArticle],
    title_vectors: Mapping[str, NDArray[np.float32]],
) -> float:
    if not title_vectors or len(articles) < 2:
        return 0.5
    vectors = np.asarray([title_vectors[article_id] for article_id in sorted(articles)])
    similarities = vectors @ vectors.T
    upper = similarities[np.triu_indices(len(vectors), 1)]
    return float(np.clip(upper.mean(), 0.0, 1.0))


def _central_related_articles(
    articles: Mapping[str, CollectedArticle],
    title_vectors: Mapping[str, NDArray[np.float32]],
) -> list[CollectedArticle]:
    if not title_vectors:
        return sorted(
            articles.values(),
            key=lambda article: (-article.published_at.timestamp(), article.article_id),
        )
    ordered = sorted(articles.values(), key=lambda article: article.article_id)
    vectors = np.asarray([title_vectors[article.article_id] for article in ordered])
    centroid = vectors.mean(axis=0)
    norm = float(np.linalg.norm(centroid))
    similarities = vectors @ (centroid / norm) if norm else np.zeros(len(ordered))
    return [
        article
        for _, article in sorted(
            zip(similarities, ordered, strict=True),
            key=lambda item: (
                -float(item[0]),
                -item[1].published_at.timestamp(),
                item[1].article_id,
            ),
        )
    ]


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
