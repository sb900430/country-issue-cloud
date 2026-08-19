from pathlib import Path

import pytest

from app.batch.keyword_translation import GlossaryKeywordTranslator
from app.schemas.issues import CountryCode


def test_repository_glossary_translates_us_and_jp_labels_to_korean() -> None:
    translator = GlossaryKeywordTranslator.load()

    assert translator.translate_to_korean(CountryCode.US, " Interest   Rate ") == "금리"
    assert translator.translate_to_korean(CountryCode.JP, "半導体") == "반도체"
    assert translator.translate_to_korean(CountryCode.KR, "기준금리") == "기준금리"


def test_unknown_label_falls_back_to_original_without_fabrication() -> None:
    translator = GlossaryKeywordTranslator.load()

    assert translator.translate_to_korean(CountryCode.US, "unlisted concept") == "unlisted concept"
    assert translator.translate_to_korean(CountryCode.JP, "未登録概念") == "未登録概念"


def test_invalid_or_incomplete_translation_glossary_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "keyword-translations.yml"
    path.write_text(
        '''schema_version: "1.0"
countries:
  US:
    Interest Rate: "금리"
    interest rate: "이자율"
  JP: {}
''',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid keyword translations"):
        GlossaryKeywordTranslator.load(path)
