# 키워드 한국어 표시 사전 / keyword韓国語表示辞書

이 문서는 미국·일본 키워드의 한국어 표시명을 관리하는 방법을 설명한다. 분석·순위는 항상 원문으로 수행하며 번역은 표시 단계에서만 적용한다.

本書は米国・日本keywordの韓国語表示名を管理する方法を説明する。分析・順位は常に原文で行い、翻訳は表示段階だけに適用する。

## 한국어

### 동작 원칙

- 원문은 Schema 2.0의 `label`, 한국어 보조명은 `label_ko`다.
- `config/keyword-translations.yml`에서 국가별 원문과 한국어 표시명을 관리한다.
- Unicode NFKC, 대소문자, 연속 공백을 정규화한 완전 일치만 허용한다.
- 미국·일본의 미등록 표현은 원문으로 표시한다. 비슷한 단어를 추측해 번역하지 않는다.
- 한국 키워드는 원문을 그대로 `label_ko`에 사용한다.
- 번역은 문서 빈도, 의미 통합, 품질 gate와 순위에 영향을 주지 않는다.
- Pages `preserve` 배포는 기존 공개 이력의 누락된 `label_ko`를 같은 사전으로 보충하며 뉴스 API를 다시 호출하지 않는다.
- 화면 전환은 미국·일본 탭에서만 표시하고 두 탭 사이에서 선택 모드를 유지한다. 한국 탭에서는 전환을 숨긴다.
- 외부 번역 API와 유료 LLM을 호출하지 않으므로 별도 Secret과 호출 비용이 없다.

### 항목 추가 방법

1. 관리자용 기사 artifact와 공개 화면에서 실제 원문 키워드의 의미를 확인한다.
2. `config/keyword-translations.yml`의 `US` 또는 `JP`에 정확한 원문과 짧은 한국어 이슈명을 추가한다.
3. 같은 정규화 원문을 중복 등록하지 않는다. 고유명사는 널리 쓰이는 한국어 표기가 확인된 경우만 등록한다.
4. `backend/tests/test_keyword_translation.py`에 중요한 회귀 사례를 추가한다.
5. `scripts/verify-all.ps1`을 실행하고 원문/한국어 전환, 상세 제목, 모바일 폭을 확인한다.

```yaml
countries:
  US:
    interest rate: "금리"
  JP:
    半導体: "반도체"
  KR: {}
```

자동 번역 provider나 local 번역 model로 교체하려면 정확도, model 용량, Actions 실행시간, 호출비용과 Secret 정책을 별도 검토하고 사용자 승인과 ADR 변경을 먼저 수행한다.

## 日本語

### 動作原則

- 原文はSchema 2.0の`label`、韓国語補助名は`label_ko`である。
- `config/keyword-translations.yml`で国別の原文と韓国語表示名を管理する。
- Unicode NFKC、大文字小文字、連続空白を正規化した完全一致だけを許可する。
- 米国・日本の未登録表現は原文表示とし、類似語を推測して翻訳しない。
- 韓国keywordは原文をそのまま`label_ko`へ使う。
- 翻訳はdocument frequency、意味統合、品質gate、順位に影響しない。
- Pagesの`preserve`配布は既存公開履歴で欠落した`label_ko`を同じ辞書で補完し、news APIを再呼出ししない。
- 画面切替は米国・日本tabだけで表示し、両tab間で選択modeを維持する。韓国tabでは切替を隠す。
- 外部翻訳API・有料LLMを呼び出さないため、追加Secret・呼出費用はない。

### 項目追加手順

1. 管理者用記事artifactと公開画面で実際の原文keywordの意味を確認する。
2. `config/keyword-translations.yml`の`US`または`JP`へ正確な原文と短い韓国語イシュー名を追加する。
3. 同じ正規化原文を重複登録しない。固有名詞は一般的な韓国語表記を確認できた場合だけ登録する。
4. `backend/tests/test_keyword_translation.py`へ重要なregression caseを追加する。
5. `scripts/verify-all.ps1`を実行し、原文/韓国語切替、詳細title、mobile幅を確認する。

```yaml
countries:
  US:
    interest rate: "금리"
  JP:
    半導体: "반도체"
  KR: {}
```

自動翻訳providerまたはlocal翻訳modelへ変更する場合は、精度、model容量、Actions実行時間、呼出費用、Secret policyを別途確認し、利用者承認とADR変更を先に行う。
