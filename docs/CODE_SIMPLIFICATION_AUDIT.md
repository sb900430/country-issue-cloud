# 코드 단순화 감사 / コード簡素化監査

- 작성일 / 作成日: 2026-08-13 JST
- 기준 commit / 基準commit: `5e00ce661f6e6c1cb7c8ac242ea433a8f5f7acb8`
- 범위 / 範囲: `backend/app`, `frontend/src`, `scripts`, package manager 설정
- 원칙 / 原則: 이 문서는 후보와 판단 근거만 기록하며 소스 코드는 변경하지 않는다. / 本文書は候補と判断根拠だけを記録し、source codeは変更しない。

## 1. 결론 / 結論

현재 코드에는 의미 없이 장황하게 풀어 쓴 대형 함수가 전반적으로 확산된 상태는 아니다. 보안 경계, 데이터 검증, 원자적 게시와 외부 API 한도 보호 때문에 필요한 코드도 많다. 따라서 줄 수만 줄이는 전면 리팩터링은 권장하지 않는다.

一方、現在のコード全体に意味なく冗長な大型関数が広がっている状態ではない。security境界、data検証、atomic配布、外部API上限保護に必要なcodeも多い。そのため、行数だけを減らす全面refactoringは推奨しない。

다만 다음 세 유형은 실제 정리 가치가 있다.

ただし、次の3種類には実際の整理価値がある。

1. 현재 Pages 운영 경로에서 사용하지 않는 과거 v1·LLM 스캐폴드
2. 공급자나 Schema 이름만 다르고 처리 흐름이 거의 같은 복제 구현
3. 실제 호출자가 없거나 선택한 도구와 중복되는 파일

우선순위는 `A > B > C`이며, A도 사용자 결정이나 회귀 테스트 없이 바로 삭제하지 않는다.

優先度は`A > B > C`とし、Aであっても利用者判断やregression testなしに直ちに削除しない。

### 적용 상태 / 適用状態

2026-08-13 첫 정리 작업에서 A-3의 `public_issue_path`, A-4, B-1, B-2, B-3, B-5와 B-6의 parser 분리를 반영했다. A-1·A-2는 제품 방향 결정이 필요해 보존했고, B-4는 v1 유지 여부가 정해지기 전 성급한 공통화를 피하기 위해 보류했다. `IncidentReporter`도 운영 연결 여부를 별도로 결정할 때까지 유지한다.

2026-08-13の初回整理作業で、A-3の`public_issue_path`、A-4、B-1、B-2、B-3、B-5、B-6のparser分離を反映した。A-1・A-2は製品方向の判断が必要なため保存し、B-4はv1維持可否の確定前に早すぎる共通化を避けるため保留した。`IncidentReporter`も運用接続可否を別途判断するまで維持する。

## 2. 품질 요약 / 品質要約

| 영역 / 領域 | 평가 / 評価 | 판단 / 判断 |
|---|---|---|
| Security | A | URL 검증, Secret 차단, 사용량 hard stop과 atomic 교체가 명확하다. / URL検証、Secret遮断、使用量hard stop、atomic置換が明確。 |
| Correctness | A- | 테스트가 충분하지만 v1·v2 병렬 경로가 변경 누락 가능성을 높인다. / testは十分だが、v1・v2並列経路が変更漏れの可能性を高める。 |
| Performance | B+ | 현재 데이터 규모에서는 문제없다. source YAML 반복 parse는 작지만 불필요하다. / 現在のdata規模では問題ない。source YAMLの反復parseは小さいが不要。 |
| Maintainability | B | 중복 publisher·repository·usage ledger와 휴면 코드가 이해 비용을 높인다. / 重複publisher・repository・usage ledgerと休眠codeが理解costを高める。 |
| Test quality | A- | 핵심 경계는 잘 검증되지만, 휴면 코드의 테스트가 전체 suite 비용을 계속 만든다. / 主要境界は十分検証されるが、休眠codeのtestがsuite costを継続的に発生させる。 |

## 3. 정리 후보 / 整理候補

### A-1. 현재 운영되지 않는 v1 이슈 파이프라인

- 근거 / 根拠:
  - 현재 workflow는 `publish-keyword-live`와 `data/v2`만 사용한다.
  - `backend/app/batch/cli.py:36-48,72-122`의 `publish-fixture`·`publish-live`는 Pages 운영 workflow에서 호출되지 않는다.
  - `backend/app/batch/live.py:32-103`의 `run_live_batch`는 v1용이며 현재 운영 함수는 `run_live_keyword_batch`다.
  - `JsonIssueRepository`, `IssuePipeline`, `StaticJsonPublisher`, `/api/v1`과 관련 테스트가 병렬 유지된다.
- 판단 / 判断: 완전히 불필요하다고 단정할 수 없다. 명세가 v1 호환 기간과 후속 FastAPI를 명시하므로 현재는 의도적으로 보존된 코드다. 다만 호환 종료 조건이 없어 영구 잔존할 위험이 가장 크다. / 完全に不要とは断定できない。仕様がv1互換期間と後続FastAPIを明示しているため、現時点では意図的な保存codeである。ただし互換終了条件がなく、恒久的に残る危険が最も大きい。
- 권장 / 推奨:
  1. v1 외부 사용자가 없음을 확인한다.
  2. VPS/EC2 재개 시 v2만 지원할지 결정한다.
  3. v1 종료 결정 시 관련 구현과 테스트를 하나의 전용 PR에서 제거한다.
- 기대 효과 / 期待効果: 가장 큰 인지 부하와 테스트 유지 비용을 제거한다. / 最大の認知負荷とtest維持costを削減する。
- 즉시 수정 / 即時修正: 하지 않음 / 実施しない。

### A-2. 실제 provider에 연결되지 않은 LLM 구현

- 근거 / 根拠:
  - `backend/app/batch/llm.py:27-116`의 cache·retry·cost 제어 구현은 테스트 외 production 조립 지점이 없다.
  - v1 `run_live_batch`도 실제 LLM 대신 `MockIssueExtractor`를 사용한다(`backend/app/batch/live.py:94-98`).
  - 현재 공개 v2 키워드는 `build_keyword_result`의 코드 기반 분석을 사용한다.
- 판단 / 判断: 향후 선택지를 미리 구현한 전형적인 선행 스캐폴드다. 지금 제품 동작에는 필요하지 않으며, provider가 정해질 때 API 계약이 달라져 다시 작성될 가능성도 있다. / 将来の選択肢を先に実装した典型的な先行scaffoldである。現在の製品動作には不要で、provider決定時にAPI契約が変わり再実装となる可能性もある。
- 권장 / 推奨: LLM 재개 계획이 없다면 `llm.py`, v1 issue clustering과 전용 테스트를 제거 대상으로 묶는다. 재개 가능성만 보존하려면 상세 구현 대신 ADR과 interface 수준만 남긴다. / LLM再開計画がなければ`llm.py`、v1 issue clustering、専用testを削除対象としてまとめる。再開可能性だけを保存する場合は詳細実装ではなくADRとinterface水準だけを残す。
- 즉시 수정 / 即時修正: 사용자 결정 전 보류 / 利用者判断まで保留。

### A-3. 사용되지 않는 작은 production API

- 근거 / 根拠:
  - `backend/app/batch/publishing.py:62`의 `public_issue_path`는 호출자가 없다.
  - `backend/app/batch/reporting.py:20-58`의 `IncidentReporter`는 테스트에서만 사용되고 batch/workflow 오류 경로에 연결되지 않는다.
- 판단 / 判断: `public_issue_path`는 제거 가능성이 높은 dead code다. `IncidentReporter`는 기능 자체보다 “구현됐지만 연결되지 않은 상태”가 문제다. / `public_issue_path`は削除可能性が高いdead codeである。`IncidentReporter`は機能自体より「実装済みだが接続されていない状態」が問題。
- 권장 / 推奨: 호출 계획이 없다면 삭제한다. Incident report가 필요하다면 먼저 실제 예외 경로에 연결하고 운영 책임을 명확히 한다. / 呼出計画がなければ削除する。Incident reportが必要なら先に実際の例外経路へ接続し、運用責任を明確にする。

### A-4. npm과 pnpm lockfile 동시 유지

- 근거 / 根拠:
  - Actions는 `npm ci`와 `frontend/package-lock.json`을 사용한다.
  - `frontend/pnpm-lock.yaml`은 실질 내용이 거의 없고 production workflow에서 사용되지 않는다.
  - `scripts/verify-all.ps1:54-69`는 npm 부재 시 pnpm으로 fallback한다.
- 판단 / 判断: 하나의 작은 frontend에 package manager 두 개를 허용하면 lockfile 불일치 가능성만 늘어난다. / 1つの小規模frontendでpackage managerを2つ許可するとlockfile不一致の可能性だけが増える。
- 권장 / 推奨: 현재 CI 기준인 npm 하나로 고정하고 pnpm lockfile과 fallback을 제거한다. / 現在のCI基準であるnpmへ統一し、pnpm lockfileとfallbackを削除する。

### B-1. 두 live batch 함수의 collector 조립 중복

- 위치 / 位置: `backend/app/batch/live.py:32-103`, `105-177`
- 문제 / 問題: GDELT gate, RSS collector, NAVER credential·ledger, NewsData credential·ledger, `CollectionRunner`, diagnostics 작성이 거의 동일하게 두 번 존재한다. / GDELT gate、RSS collector、NAVER credential・ledger、NewsData credential・ledger、`CollectionRunner`、diagnostics作成がほぼ同じ形で2回存在する。
- 권장 / 推奨: `_build_collectors(...)`와 `_collect_live_articles(...)` 정도의 작은 내부 함수만 추출한다. 결과 생성·게시 부분은 v1/v2별로 유지한다. / `_build_collectors(...)`と`_collect_live_articles(...)`程度の小さな内部関数だけを抽出し、結果生成・配布部分はv1/v2別に維持する。
- 주의 / 注意: 범용 pipeline framework나 복잡한 class hierarchy까지 만들면 오히려 AI식 과잉 추상화가 된다. / 汎用pipeline frameworkや複雑なclass hierarchyまで作ると、かえってAI的な過剰抽象化となる。

### B-2. NAVER·NewsData 사용량 장부 복제

- 위치 / 位置: `backend/app/batch/naver_usage.py:43-93`, `backend/app/batch/newsdata_usage.py:36-86`
- 문제 / 問題: 날짜 전환, JSON load/save, lock, daily/monthly 증가 로직이 사실상 동일하다. provider별 차이는 timezone, 기본 한도와 오류 문구다. / 日付切替、JSON load/save、lock、daily/monthly増加logicが実質的に同一。provider別差分はtimezone、標準上限、error文言。
- 권장 / 推奨: 파일 저장과 카운터 증가만 담당하는 작은 공통 `UsageLedger`를 두고 provider policy는 현재 class로 유지한다. / file保存とcounter増加だけを担当する小さな共通`UsageLedger`を置き、provider policyは現在のclassとして維持する。
- 기대 효과 / 期待効果: 한도 장부 오류 수정이 한 곳에서 이뤄지고 테스트 중복도 줄어든다. / 上限ledgerの修正箇所が1つとなり、test重複も減る。

### B-3. v1·v2 정적 publisher 복제

- 위치 / 位置: `backend/app/batch/publishing.py:9-60`, `backend/app/batch/keyword_publishing.py:8-57`
- 문제 / 問題: 최근 7일 선택, latest 일치 검증, 임시 directory, backup, rollback, `dates.json` 생성이 거의 같다. / 最新7日選択、latest一致検証、一時directory、backup、rollback、`dates.json`生成がほぼ同一。
- 권장 / 推奨: 원자적 directory 교체와 history 복사를 내부 helper로 공유하고 Schema 검증과 filename pattern만 주입한다. / atomic directory置換とhistory copyを内部helperで共有し、Schema検証とfilename patternだけを注入する。
- 주의 / 注意: A-1에서 v1 제거를 결정한다면 먼저 추상화하지 말고 v1 삭제 후 남은 v2 구현을 유지한다. / A-1でv1削除を決めるなら先に抽象化せず、v1削除後に残るv2実装を維持する。

### B-4. JSON repository 복제

- 위치 / 位置: `backend/app/repositories/json_issue_repository.py:17-104`, `backend/app/repositories/json_keyword_repository.py:17-85`
- 문제 / 問題: date 검색, latest 읽기, 기간 필터, model validation, atomic write가 중복된다. / date検索、latest読込、期間filter、model validation、atomic writeが重複する。
- 권장 / 推奨: v1 유지가 확정될 때만 file 탐색·atomic write를 private helper로 공유한다. Pydantic generic repository까지 도입할 필요는 없다. / v1維持が確定した場合だけfile探索・atomic writeをprivate helperで共有する。Pydantic generic repositoryまで導入する必要はない。

### B-5. source 설정을 한 실행에서 여러 번 parse

- 위치 / 位置: `backend/app/batch/source_config.py:63-204`, `backend/app/batch/cli.py:90-153`
- 문제 / 問題: 각 `load_*_sources(path)`가 같은 YAML을 다시 읽고 전체 entry를 다시 순회한다. 현재 파일이 작아 성능 문제는 아니지만 흐름이 길고 validation 책임이 분산된다. / 各`load_*_sources(path)`が同じYAMLを再読込し、全entryを再走査する。現在のfileは小さく性能問題ではないが、flowが長くvalidation責任が分散する。
- 권장 / 推奨: CLI에서 `SourceRegistry`를 한 번 읽고 `build_rss_sources(registry)`처럼 변환 함수에 전달한다. / CLIで`SourceRegistry`を1回読み、`build_rss_sources(registry)`のような変換関数へ渡す。

### B-6. CLI의 단일 대형 분기

- 위치 / 位置: `backend/app/batch/cli.py:33-188`
- 문제 / 問題: parser 정의와 6개 command 실행이 `main()` 하나에 모여 있어 v1/v2 중복을 더 크게 보이게 한다. / parser定義と6 command実行が1つの`main()`へ集中し、v1/v2重複をより大きく見せている。
- 권장 / 推奨: `_build_parser()`와 command별 `_run_*()` 함수로만 분리한다. 별도 command framework 도입은 불필요하다. / `_build_parser()`とcommand別`_run_*()`関数へだけ分離する。別command framework導入は不要。

### C-1. 일반 제외어와 운영 금지어의 이중 관리

- 위치 / 位置: `backend/app/batch/keywords.py:24-114`, `config/keyword-blocklist.yml`
- 문제 / 問題: 일반어는 Python 상수, 정치·운영 금지어는 YAML에서 관리되어 사용자가 “제외어”를 찾을 때 두 위치를 확인해야 한다. `keywords.py` 439줄 중 상당 부분이 데이터 목록이다. / 一般語はPython定数、政治・運用禁止語はYAMLで管理され、「除外語」を探す際に2か所を確認する必要がある。`keywords.py` 439行の一部はdata一覧。
- 권장 / 推奨: category를 구분한 하나의 검증된 YAML Schema로 옮길지 검토한다. 성능상 상수 유지가 더 단순하다면 현재 구조를 유지하되 두 목록의 차이를 guide에 명확히 적는다. / categoryを分けた1つの検証済みYAML Schemaへ移すか検討する。性能上定数維持が単純なら現状を維持し、2種類の差をguideへ明記する。
- 판단 / 判断: 길다는 이유만으로 즉시 분리할 항목은 아니다. / 長いという理由だけで即時分離する項目ではない。

## 4. 유지해야 하는 코드 / 維持すべきコード

다음 항목은 겉보기에는 길거나 방어적이지만 현재 요구사항상 불필요한 코드로 보지 않는다.

次の項目は見た目には長い、または防御的だが、現在要件上の不要codeとは判断しない。

- `backend/app/batch/keywords.py`의 언어별 형태소 처리와 TOP 5 품질 gate: 제품 핵심 로직이며 테스트가 충분하다. / 言語別形態素処理とTOP 5品質gateは製品核心logicでtestも十分。
- `scripts/build-pages-site.ps1`의 경로 검증과 기존 Pages 보존 처리: destructive path와 배포 실패를 막는 안전장치다. / path検証と既存Pages保存処理はdestructive pathと配布失敗を防ぐ安全装置。
- `frontend/src/data-source.js`의 Static/API adapter: 현재 Static만 운영하지만 VPS/EC2 전환 경계로 명세에 명시되어 있다. / 現在はStaticのみ運用だが、VPS/EC2移行境界として仕様に明記される。
- `frontend/src/app.js`의 상태·event·dialog 처리: 195줄이지만 한 화면 규모에 맞고 불필요한 framework나 class 분할이 없다. / 195行だが1画面規模に適合し、不要なframeworkやclass分割がない。
- atomic write, backup rollback, usage hard stop, SSRF 방지: 중복 정리는 가능하지만 안전 검사를 줄이면 안 된다. / atomic write、backup rollback、usage hard stop、SSRF防止は重複整理可能だが安全検査を減らしてはならない。

## 5. 권장 실행 순서 / 推奨実行順序

1. 사용자 결정: v1과 LLM 상세 구현을 계속 보존할지 확정한다. / 利用者判断: v1とLLM詳細実装を継続保存するか確定する。
2. 확실한 dead code와 package manager 중복을 작은 PR로 제거한다. / 明確なdead codeとpackage manager重複を小さなPRで削除する。
3. v1 제거 시 publisher·repository의 공통화는 하지 않고 v1 코드를 먼저 삭제한다. / v1削除時はpublisher・repository共通化を行わず、v1 codeを先に削除する。
4. v1 유지 시 live collector 조립, usage ledger, publisher의 작은 공통 helper만 도입한다. / v1維持時はlive collector組立、usage ledger、publisherの小さな共通helperだけを導入する。
5. source config를 한 번만 읽도록 정리하고 CLI command handler를 분리한다. / source configを1回だけ読むよう整理し、CLI command handlerを分離する。
6. 각 단계에서 전체 테스트 수가 아니라 변경 코드의 가독성, 중복 감소와 안전 gate 보존 여부를 검토한다. / 各段階でtest総数ではなく、変更codeの可読性、重複削減、安全gate維持を確認する。

## 6. 이번 감사에서 변경하지 않은 것 / 今回変更しなかったもの

- production source code
- test code
- dependency와 lockfile
- API Schema와 workflow
- 한국어·일본어 명세

이 문서의 후보는 별도 승인된 리팩터링 작업에서만 반영한다.

本文書の候補は、別途承認されたrefactoring作業でのみ反映する。
