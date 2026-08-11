import unicodedata
from datetime import date
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.issues import CountryCode

DEFAULT_KEYWORD_BLOCKLIST_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "keyword-blocklist.yml"
)


class KeywordBlockMatch(StrEnum):
    EXACT = "exact"
    CONTAINS = "contains"


class KeywordBlockRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    term: str = Field(min_length=2, max_length=80)
    match: KeywordBlockMatch = KeywordBlockMatch.EXACT
    category: str = Field(min_length=1, max_length=40)
    reason_ko: str = Field(min_length=1, max_length=200)
    reason_ja: str = Field(min_length=1, max_length=200)
    added_on: date
    enabled: bool = True


class KeywordBlocklistConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(pattern=r"^1\.0$")
    countries: dict[CountryCode, tuple[KeywordBlockRule, ...]]

    @model_validator(mode="after")
    def validate_country_rules(self) -> "KeywordBlocklistConfig":
        if set(self.countries) != set(CountryCode):
            raise ValueError("keyword blocklist must define US, JP and KR")
        for country, rules in self.countries.items():
            identities = [(_normalize(rule.term), rule.match) for rule in rules]
            if len(identities) != len(set(identities)):
                raise ValueError(f"keyword blocklist contains duplicate rules for {country.value}")
        return self


class KeywordBlocklist:
    def __init__(self, config: KeywordBlocklistConfig) -> None:
        self.config = config

    @classmethod
    def load(cls, path: Path = DEFAULT_KEYWORD_BLOCKLIST_PATH) -> "KeywordBlocklist":
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            return cls(KeywordBlocklistConfig.model_validate(payload))
        except (OSError, yaml.YAMLError, ValueError) as error:
            raise ValueError(f"Invalid keyword blocklist: {path.name}") from error

    def blocks(self, country: CountryCode, label: str) -> bool:
        candidate = _normalize(label)
        for rule in self.config.countries[country]:
            if not rule.enabled:
                continue
            term = _normalize(rule.term)
            if rule.match is KeywordBlockMatch.EXACT and candidate == term:
                return True
            if rule.match is KeywordBlockMatch.CONTAINS and term in candidate:
                return True
        return False


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
