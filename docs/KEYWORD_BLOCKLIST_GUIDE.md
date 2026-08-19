# 국가별 금지 키워드 관리 가이드

## 목적

운영 결과에서 정치인·정당명처럼 경제 이슈 상위 3~5개에 적합하지 않은 표현을 발견하면 `config/keyword-blocklist.yml`에 국가별 규칙으로 추가한다. 코드 상수를 수정하지 않아도 목록을 점진적으로 확장할 수 있고 모든 변경은 Git 이력으로 남는다.

## 규칙 형식

```yaml
countries:
  KR:
    - term: "오세훈"
      match: "contains"
      category: "politics"
      reason_ko: "정치인 이름으로 경제 이슈 키워드에서 제외"
      reason_ja: "政治家名のため経済issue keywordから除外"
      added_on: "2026-08-11"
      enabled: true
```

- `term`: 차단할 원문 표현이며 두 글자 이상이어야 한다.
- `match: exact`: 후보 전체가 `term`과 같을 때만 제외한다. 일반적으로 우선 선택한다.
- `match: contains`: 후보 안에 `term`이 포함되면 제외한다. 인명·정당 약칭처럼 결합형도 차단해야 할 때만 사용한다.
- `category`: `politics`, `person`, `template`, `noise`처럼 제외 유형을 기록한다.
- `reason_ko`, `reason_ja`: 한국어·일본어로 같은 제외 근거를 기록한다.
- `added_on`: JST 기준 추가 날짜다.
- `enabled`: `false`이면 기록은 유지하지만 필터는 적용하지 않는다.

## 추가 절차

1. 비공개 관리자 Actions artifact의 `selected-articles.json`과 실제 상위 키워드를 확인한다.
2. 여러 기사에서 반복되지만 프로젝트의 경제 이슈 목적과 무관한 표현인지 확인한다.
3. 해당 국가 목록에 규칙을 추가하고, 오탐 위험이 낮은 `exact`를 먼저 사용한다.
4. 한국어·일본어 사유와 추가일을 기록한다.
5. 키워드 회귀 테스트와 `scripts/verify-all.ps1`을 실행한다.
6. PR에서 근거와 영향 범위를 확인한 뒤 병합한다.

설정 파일이 없거나 Schema가 잘못되거나 같은 국가에 동일 규칙이 중복되면 배치는 실패한다. 이때 기존 정상 Pages 결과는 유지된다. 운영 중 즉시 되돌려야 하면 규칙을 삭제하기보다 `enabled: false`로 변경해 이력을 보존한다.
