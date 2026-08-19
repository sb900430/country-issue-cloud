# Weekly Review Guide / 주간 리뷰 가이드 / 週次レビューガイド

## 1. 실행 기준 / Execution

| 항목 | 기준 |
|---|---|
| 실행 시점 | 활성 주차의 구현·테스트·문서·전체 검증 완료를 감지한 즉시 |
| 검토 시간 제한 | 최대 60분 |
| Critical/High 수정 시간 | 리뷰 종료 후 최대 90분 |
| 명령별 기본 timeout | 20분, Android 전체 검증은 30분 |
| 일시적 실패 재시도 | 원인 확인 후 1회 |
| 동일 항목 수정 시도 | 최대 2회, 이후 `BLOCKED` |
| 결과 파일 | `reviews/YYYY-MM-DD-weekly-review.md` (로컬 전용) |
| 상세 템플릿 | `docs/review/WEEKLY_REVIEW_TEMPLATE.md` |

60분이 지나면 남은 검사를 숨기지 않고 `NOT_RUN`으로 기록한다. 네트워크·도구 문제처럼 일시적인 실패만 한 번 재시도하며, 같은 코드에서 반복되는 결정적 테스트 실패는 재시도하지 않고 finding으로 기록한다.

日本語：レビュー本体は最大60分、Critical/High修正は別枠で最大90分とする。一時的な失敗だけ原因確認後に1回再試行し、同一findingの修正は2回までとする。
実行時点は固定曜日ではなく、active週の実装・test・文書・全検証の完了を検知した直後とする。

## 2. 비교 범위 / Review range

- `reviews/.last-reviewed-sha`부터 현재 `HEAD`까지의 commit과 diff를 기본 범위로 사용한다.
- 첫 리뷰에서는 전체 저장소의 보안·설정 검사와 최근 7일 diff를 검토한다.
- 리뷰가 정상 완료된 경우에만 `.last-reviewed-sha`를 현재 `HEAD`로 갱신한다.
- diff 밖에서 발견한 기존 문제는 `LEGACY`로 구분한다. Critical/High는 기존 문제라도 수정 대상이다.
- 생성물, build output, 외부 vendor 코드는 직접 리뷰하지 않되 생성 과정과 checksum/lockfile은 확인한다.

日本語：基本範囲は`.last-reviewed-sha`から`HEAD`までとする。初回はリポジトリ全体のsecurity/configと直近7日diffを確認し、完了時だけ基準SHAを更新する。

## 3. 필수 검사 순서 / Required order

1. 작업 트리, 기준 SHA, commit/PR 범위를 기록한다.
2. `git diff --check`와 한·일 명세 동기화를 검사한다.
3. secret, 위험 설정, 입력 검증, 의존성 취약점을 검사한다.
4. `scripts/verify-all.ps1`로 lint, type check, test, build를 실행한다.
5. 변경 코드와 핵심 경로의 테스트 커버리지를 확인한다.
6. 정확성, 성능, 유지보수성, 문서·아키텍처 준수를 diff 중심으로 리뷰한다.
7. LLM 또는 UI 변경이 있으면 해당 회귀 검사를 추가한다.
8. finding을 심각도순으로 기록하고 Critical/High를 수정·재검증한다.
9. 결과 상태와 다음 조치를 기록하고 기준 SHA를 갱신한다.

## 4. 커버리지 기준 / Coverage thresholds

| 대상 | Line | Branch | 비고 |
|---|---:|---:|---|
| 이번 리뷰 변경 코드 | 80% | 70% | 언어 공통 우선 기준 |
| Python backend 전체 | 80% | 70% | 집계·Repository·검증 핵심 경로는 Line 90% |
| Web 전체 | 75% | 65% | 상태 처리와 API 변환 우선 |
| Android JVM 전체 | 70% | 60% | ViewModel·Repository는 Line 80% |

- scaffold 전이거나 테스트 도구가 아직 없는 모듈은 `SKIP`과 이유를 기록한다.
- 테스트가 도입된 모듈은 기준 미달을 Medium으로 기록한다. 핵심 로직이 무검증이면 High로 올릴 수 있다.
- 생성 코드, build output, 단순 DTO/getter, 외부 라이브러리는 분모에서 제외할 수 있으며 제외 목록을 설정에 명시한다.
- 전체 커버리지가 기존보다 2%p 이상 감소하면 최소 Medium finding을 만든다.

日本語：変更コード80%、backend 80%、Web 75%、Android 70%をline coverageの標準値とする。主要ロジック未検証はHigh候補、全体2ポイント以上低下はMedium以上とする。

## 5. 영역별 체크리스트 / Review checklist

### Security

- secret, token, 인증 header, 개인정보가 코드·로그·fixture·문서에 없는가
- path traversal, injection, XSS, SSRF, 안전하지 않은 역직렬화 가능성이 없는가
- 외부 URL과 날짜·국가 입력을 allowlist/Schema로 검증하는가
- Android 앱에 서버 비밀키가 없고 release에서 HTTPS를 강제하는가
- Critical/High 취약 의존성이 없는가

### Correctness

- 빈 입력, null, 잘못된 시간, 중복, 동률, 부분 성공을 처리하는가
- 국가별 실패가 다른 국가 결과를 오염시키지 않는가
- 배치가 idempotent하며 lock·원자적 저장·latest 보호가 동작하는가
- 오래된 비동기 응답이 최신 Android 상태를 덮지 않는가
- API Schema와 Room/DTO 변환이 일치하는가

### Performance

- 무제한 loop/query, O(n²) hot path, N+1, resource leak이 없는가
- 캐시 적중 로컬 API p95가 500ms 이하인가
- fixture 기반 비캐시 API p95가 1초 이하인가
- mock 기반 3개국 pipeline이 개발 PC에서 60초 이내인가
- 국가 탭 전환이 추가 network request를 만들지 않는가

성능 기준은 동일한 로컬 환경에서 3회 실행한 중앙값을 사용한다. 대규모 load test와 Android macrobenchmark는 월간 또는 출시 게이트에서 수행한다.

### Maintainability and architecture

- UI → ViewModel → Repository → Room/API 경계와 API/batch import 경계를 지키는가
- 중복, 과도한 책임, 불명확한 이름과 불필요한 의존성이 없는가
- 메서드 단위 설명 주석과 TODO/FIXME 설명이 일본어인가
- 한국어·일본어 명세, 개발 상태와 일일 보고서가 동기화됐는가
- 목표 범위, 브랜치, PR, commit subject, Rebase and merge 정책을 준수하는가

### Test quality

- 새 동작과 오류 경로에 테스트가 있는가
- mock/fixture가 실제 계약과 일치하며 외부 API/LLM을 기본 CI에서 호출하지 않는가
- flaky test, 의미 없는 assertion, 과도한 snapshot이 없는가
- UI 기준 이미지 변경을 사람이 승인했는가

## 6. LLM 품질 기준 / LLM quality gates

LLM·prompt·cluster 변경이 있을 때 다음을 검사한다.

| 항목 | 기준 |
|---|---:|
| Schema 유효성 | 100% |
| 입력에 없는 article ID/근거 표현 | 0건 |
| 국가 간 데이터 혼합 | 0건 |
| 상위 3~5개 중복 issue | 0건 |
| 코드 순위 결정성 | 100% |
| 추출 성공률 | 80% 이상 |
| 수동 label 표본 | 국가별 최대 5개, 80% 이상 수용 가능 |

불변조건 위반은 데이터 신뢰도에 따라 High 또는 Critical로 분류한다. 단순 label 표현 개선은 Medium/Low로 기록할 수 있다.

## 7. 심각도 판정 / Severity

| 심각도 | 구체 기준 | 예시 |
|---|---|---|
| Critical | 비밀 유출, 원격 악용, 게시 데이터 파괴, 전체 서비스 불능 | API key commit, 임의 파일 접근, latest 영구 손상 |
| High | 핵심 기능 오류, 잘못된 국가/순위, 주요 보안 경계 위반, 핵심 로직 무테스트 | 국가 간 기사 혼합, release HTTP, 원자적 저장 실패 |
| Medium | 제한적 오류, 커버리지 미달, 성능 저하, 유지보수 위험 | 오류 상태 누락, 전체 coverage 2%p 하락 |
| Low | 동작에 영향이 적은 명명·구조·문서 개선 | 중복 표현, 작은 가독성 문제 |

## 8. 반복 finding 관리 / Finding lifecycle

- finding ID는 `WR-YYYYMMDD-NNN` 형식을 사용한다.
- 같은 파일·규칙·원인의 항목은 fingerprint로 식별하고 중복 생성하지 않는다.
- 상태는 `OPEN`, `RESOLVED`, `ACKNOWLEDGED`, `BLOCKED`를 사용한다.
- Medium이 3회 연속, Low가 4회 연속 남으면 우선 검토 대상으로 표시하지만 기간만으로 심각도를 자동 승격하지 않는다.
- 수정된 finding은 원래 재현 절차와 회귀 테스트로 확인한 뒤 `RESOLVED` 처리한다.

## 9. 리뷰 최종 상태 / Review result

| 상태 | 조건 |
|---|---|
| `PASS` | Critical/High 없음, 필수 검사 완료 |
| `PASS_WITH_FINDINGS` | Medium/Low만 존재, 필수 검사 완료 |
| `FAIL` | Critical/High 미해결 또는 필수 검증 실패 |
| `BLOCKED` | 도구·권한·외부 결정 때문에 필수 검사를 완료하지 못함 |

Critical/High 수정은 `codex/review-fix-YYYY-MM-DD` branch와 Draft PR을 사용한다. 수정 시도 2회 또는 수정 시간 90분을 넘으면 `BLOCKED`로 남기고 사용자 판단을 요청한다.
