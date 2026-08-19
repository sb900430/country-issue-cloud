import unicodedata
from pathlib import Path
from typing import Annotated, Literal, Protocol

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.issues import CountryCode
from app.schemas.keywords import KeywordResult

DEFAULT_KEYWORD_TRANSLATIONS_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "keyword-translations.yml"
)


class KeywordTranslator(Protocol):
    def translate_to_korean(self, country: CountryCode, label: str) -> str: ...


class KeywordTranslationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    countries: dict[
        CountryCode,
        dict[
            Annotated[str, Field(min_length=1, max_length=80)],
            Annotated[str, Field(min_length=1, max_length=80)],
        ],
    ]

    @model_validator(mode="after")
    def validate_country_entries(self) -> "KeywordTranslationConfig":
        if set(self.countries) != set(CountryCode):
            raise ValueError("keyword translations must define US, JP and KR")
        for country, entries in self.countries.items():
            normalized = [_normalize(label) for label in entries]
            if len(normalized) != len(set(normalized)):
                raise ValueError(
                    f"keyword translations contain duplicate labels for {country.value}"
                )
        return self


class GlossaryKeywordTranslator:
    def __init__(self, config: KeywordTranslationConfig) -> None:
        self.entries = {
            country: {_normalize(label): translated for label, translated in entries.items()}
            for country, entries in config.countries.items()
        }

    @classmethod
    def load(
        cls,
        path: Path = DEFAULT_KEYWORD_TRANSLATIONS_PATH,
    ) -> "GlossaryKeywordTranslator":
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            return cls(KeywordTranslationConfig.model_validate(payload))
        except (OSError, yaml.YAMLError, ValueError) as error:
            raise ValueError(f"Invalid keyword translations: {path.name}") from error

    def translate_to_korean(self, country: CountryCode, label: str) -> str:
        if country is CountryCode.KR:
            return label
        return self.entries[country].get(_normalize(label), label)


def apply_korean_keyword_labels(
    result: KeywordResult,
    translator: KeywordTranslator,
) -> KeywordResult:
    return result.model_copy(
        update={
            "countries": {
                country: country_result.model_copy(
                    update={
                        "top_keywords": [
                            keyword.model_copy(
                                update={
                                    "label_ko": translator.translate_to_korean(
                                        country, keyword.label
                                    )
                                }
                            )
                            for keyword in country_result.top_keywords
                        ]
                    }
                )
                for country, country_result in result.countries.items()
            }
        }
    )


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
