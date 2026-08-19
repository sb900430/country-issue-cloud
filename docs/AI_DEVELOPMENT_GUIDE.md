# AI 개발 가이드

이 문서는 AI와 함께 빠르게 개발하면서 범위 이탈, 검증 누락, 문맥 손실을 방지하기 위한 실행 규칙이다. 제품 요구사항은 `PROJECT_SPEC.md`, 일본어판은 `PROJECT_SPEC_JA.md`를 따른다.

## 1. 고정 기술 선택

| 영역 | 선택 |
|---|---|
| Python 환경·패키지 | `uv`, `pyproject.toml`, lockfile 커밋 |
| API | FastAPI, Pydantic v2 계열 |
| Web(현재 우선) | Semantic HTML/CSS/Vanilla JS, Fetch API, npm 기반 검사·테스트 |
| Web 상태·저장 | JavaScript 상태 모듈, localStorage, Cache API 또는 IndexedDB |
| 데이터 접근 | `IssueDataSource`; 기본 Static JSON, 후속 FastAPI adapter |
| 1차 운영 | GitHub Actions schedule/workflow_dispatch + GitHub Pages artifact |
| 후속 운영 | VPS/EC2 + FastAPI, DataSource 설정만 전환 |
| Android(보류) | 재개 시 Retrofit, Kotlinx Serialization, ViewModel, Flow, Room, DataStore, Hilt 재검증 |
| 날짜·시간 | 서버 UTC 저장, `Asia/Tokyo` 표시 |
| 뉴스 수집 목표 | NewsData.io·NAVER와 공공 RSS/API, GDELT 429 해소 전 보류, 국가별 150건 목표·250건 상한 |
| 키워드 분석 | 구성 단어·복합명사 보존 → 국가별 YAML 금지어 → local 다국어 embedding 제한 병합·기사 응집도 → 2%·3건·정규화 2매체 gate → 일반어·중복 이슈 제거 → 품질 3~5개 순위 |

정확한 라이브러리 버전은 스캐폴드 시점의 공식 안정 버전을 확인해 고정하고 lockfile 또는 version catalog에 기록한다. 의존성을 임의로 추가하지 말고 표준 기능으로 해결하기 어려운 경우에만 도입 이유를 ADR에 남긴다.

## 2. AI 작업 요청 계약

모든 구현 작업은 다음 정보를 기준으로 수행한다.

```md
## 작업 목표
사용자가 확인할 수 있는 결과

## 작업 범위
수정 가능한 기능과 디렉터리

## 제외 범위
이번 작업에서 변경하지 않을 항목

## 완료 조건
- 기능 요구사항
- 필수 테스트
- 문서 동기화 여부

## 검증 명령
실행할 명령과 기대 결과

## 주차 커밋
개발 주차와 최종 커밋 메시지
```

요청에 일부 항목이 없어도 명세와 현재 코드에서 안전하게 확인 가능한 내용은 AI가 보완한다. 비용, 외부 계약, 공개 범위, 자격증명, 되돌리기 어려운 변경처럼 사용자의 판단이 필요한 경우에는 작업 전에 질문한다.

## 3. 작업 순서

1. `AGENTS.md`, 양쪽 명세, `docs/DEVELOPMENT_STATUS.md`를 읽는다.
2. `main`을 최신화하고 해당 주차의 `codex/week-*` 브랜치를 만든다.
3. `git status`로 사용자 변경사항을 확인하고 보존한다.
4. 요구사항, 영향 파일, 검증 기준을 확인한다.
5. 가장 작은 완결 단위로 구현하고 관련 테스트를 실행한다.
6. 한국어·일본어 명세에 영향을 주면 두 파일을 함께 수정한다.
7. `scripts/verify-all.ps1`을 실행한다.
8. 그날 개발 작업이 있었다면 `docs/daily/YYYY-MM-DD.md` 일일 보고서를 작성하고 개발 상태 문서를 갱신한다.
9. WIP 커밋을 squash해 주차 단위 커밋 하나로 정리한다.
10. 주차 브랜치를 push하고 `main` 대상 Draft PR 하나를 만든다.
11. CI와 리뷰가 통과하면 Ready로 전환하고 **Rebase and merge**로 병합한다.
12. 최신 `main`으로 전환해 `scripts/verify-all.ps1`과 가능한 로컬 smoke test를 다시 실행한다.
13. 병합 후 검증이 통과한 경우에만 해당 주차를 완료 처리하고 다음 주차 브랜치를 만든다.

## 4. 일일 개발 보고서

- 개발 작업이 수행된 날의 종료 시점에 `docs/daily/TEMPLATE.md`를 복사해 `docs/daily/YYYY-MM-DD.md`를 작성한다.
- 하나의 파일 안에 같은 의미의 한국어와 일본어 섹션을 모두 작성한다.
- 날짜는 `Asia/Tokyo` 기준이며 같은 날짜 파일이 있으면 새 파일을 만들지 않고 갱신한다.
- 오늘의 목표, 수행 작업, 주요 변경 파일, 검증 명령과 PASS/FAIL/SKIP, 결정사항, 문제·리스크, 다음 작업을 포함한다.
- 실패나 미완료 작업도 숨기지 않고 원인과 다음 조치를 남긴다.
- API 키, 토큰, 인증 헤더, 개인정보와 원문 로그 전체를 기록하지 않는다.
- 일일 보고서는 Git 추적 대상이며 현재 주차 브랜치에 보관한다. 일일 보고서만을 위한 별도 커밋은 만들지 않고 주차 최종 커밋과 PR에 포함한다.
- 주차 완료 감지 리뷰의 `reviews/` 파일은 로컬 전용이므로 일일 보고서와 분리한다.

## 5. 공통 Definition of Done

- 요구 기능과 오류 경로가 구현되었다.
- 새 동작을 검증하는 단위 또는 통합 테스트가 있다.
- 기존 테스트, lint, type check, build가 통과한다.
- 외부 API와 LLM은 기본 테스트에서 mock/fixture를 사용한다.
- 로그, 오류, fixture, 문서에 비밀정보가 없다.
- `scripts/check-secrets.ps1`이 통과하고 금지된 credential 파일이 Git 추적 대상이 아니다.
- 실행·설정·계약 변경은 관련 문서에 반영했다.
- 명세 변경 시 한국어판과 일본어판을 같은 작업에서 수정했다.
- 메서드 단위 설명 주석과 TODO/FIXME 설명은 일본어다.
- 개발한 각 날짜의 일일 보고서가 작성되어 있다.
- 주차 커밋 하나만 checkout해도 해당 주차 결과를 빌드·테스트할 수 있다.
- Pages 대상 변경은 fixture artifact build, 공개 JSON Schema와 Secret 검사를 통과한다.

## 6. AI 변경 제한

- 요청 없이 API v1의 기존 필드 의미를 바꾸지 않는다.
- 국가별 독립 처리 원칙과 API/배치 import 경계를 깨지 않는다.
- 테스트를 통과시키기 위해 검증을 삭제하거나 약화하지 않는다.
- 실제 뉴스 API나 LLM을 단위 테스트에서 호출하지 않는다.
- 사용자 변경, 운영 데이터, 리뷰 파일을 덮어쓰거나 Git에 추가하지 않는다.
- 기술 스택 또는 핵심 구조를 바꿀 때는 ADR과 사용자 확인이 필요하다.
- 보호되지 않은 HTTP, 앱 내 비밀키, 원문 전체 저장을 허용하지 않는다.
- 웹 UI에서 정적 JSON 또는 `/api/v1`·`/api/v2` 경로를 직접 분산 참조하지 않고 DataSource 경계를 사용한다.
- 실제 뉴스·LLM Secret은 PR workflow에서 사용하지 않고 보호된 운영 workflow에서만 사용한다.
- v2 구현 전 기존 v1의 `top_issues` 의미를 바꾸지 않고, producer·DataSource·Web을 함께 전환한다.

## 7. LLM 회귀 검증

`sample-data/evaluation/{US,JP,KR}`에 고정 기사 입력을 두고 `sample-data/evaluation/expected`에 검증 기대값을 둔다. 문장 전체 일치 대신 다음 불변조건을 검사한다.

- 출력 Schema가 유효하다.
- 입력에 없는 기사 ID와 근거 표현이 없다.
- 국가 간 기사와 이슈가 섞이지 않는다.
- 동일 입력의 코드 순위가 결정적이다.
- 상위 3~5개에 중복 이슈가 없다.
- 국가별 100건 이상 입력에서 일반어·언론사명·정치인 이름이 상위 결과에 포함되지 않고 복합명사와 관련 기사 연결이 보존된다.
- 호출량과 비용 상한을 기록한다.

실제 모델 평가는 명시적인 live/evaluation 작업에서만 실행하고 기본 CI에서는 mock을 사용한다.

## 8. UI 회귀 검증

웹 스크린샷 기준은 기본 타일형, 클라우드형, 로딩, 부분 성공, 캐시 복구, 작은 화면, 글자 확대, 긴 다국어 라벨을 포함한다. 차이가 발생하면 자동 승인하지 않고 이미지와 의도된 변경을 사람이 확인한다. Android 재개 시 같은 상태의 Compose 기준을 별도로 추가한다.

## 9. 커밋과 복구

모든 커밋 제목은 `YYYY/MM/DD <type>: <English> | <한국어> | <日本語>` 형식을 사용한다. 날짜는 실제 커밋 날짜이고 세 요약은 같은 의미로 작성한다. 주차별 브랜치에서 WIP 커밋을 사용할 수 있으나 주차 완료 감지 리뷰와 Critical/High 수정 후 squash 또는 amend하여 주차 커밋 하나만 남긴다. 주차 브랜치를 push해 Draft PR 하나를 만들고 **Rebase and merge**로 `main`에 병합한다. 후보 커밋을 리뷰 후 수정하는 경우 `--force-with-lease`만 허용한다. `Create a merge commit`은 사용하지 않으며 `Squash and merge`는 로컬 정리가 불가능한 예외에만 허용한다. 병합 후 최신 `main`에서 전체 검증과 smoke test를 실행하고, 실패하면 `codex/post-merge-fix-week-<number>` 브랜치와 별도 PR로 수정한다. 완료 후 상태 문서에 주차, PR 번호, 커밋 SHA와 병합 후 검증 결과를 기록한다.

## 10. 표준 명령

```powershell
.\scripts\check-spec-sync.ps1
.\scripts\check-secrets.ps1
.\scripts\verify-all.ps1
```

개별 프로젝트가 아직 생성되지 않은 단계에서는 해당 검사를 `SKIP`으로 표시한다. 스캐폴드가 존재하는데 필수 도구나 테스트가 실행되지 않으면 실패로 처리한다.
