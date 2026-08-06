# 개발 진행 상태

| 항목 | 현재 상태 |
|---|---|
| 현재 목표 | 3주차 — 반응형 웹·GitHub Pages MVP |
| 상태 | 3주차 병합 완료 — Pages 출력 경로 수정·검증 완료 |
| 기준 브랜치 | `main` |
| 작업 브랜치 | `codex/post-merge-fix-week-03` |
| 마지막 완료 커밋 | `6bee3b9` — 3주차 PR #9 Rebase and merge |
| 전체 검증 | PASS — `dist/site` artifact·Python 62개·웹 6개·Ruff·mypy·Secret·명세 |
| 다음 작업 | 병합 후 수정 Draft PR 생성과 CI 확인 |

## 3주차 진행 결과

- 미국은 Federal Reserve·BLS RSS, 일본은 METI Atom·BOJ RSS, 한국은 한국은행 RSS를 활성 후보로 확정했다.
- BEA·e-Stat은 등록 정보가 필요하므로 기본 비활성으로 기록했다.
- 두 조건부 API의 사용자 등록, Secret 보관, 어댑터 구현과 활성화 체크리스트를 한·일 설명서로 작성했다.
- KDI 대신 별도 등록이 없는 금융위원회 보도자료·보도설명 RSS와 중소벤처기업부 보도자료 RSS를 활성 후보로 반영했다.
- 공식 RSS 실연동으로 미국 7건·일본 28건·한국 27건과 Pages JSON 생성을 검증했다.
- BLS는 자동 요청 403, METI는 6월 이후 미갱신을 확인해 상태가 바뀔 때까지 비활성으로 전환했다.
- 소스별 허용 필드, 이용조건 확인일과 90일 재검토일을 설정에 반영했다.
- RSS 2.0과 Atom을 같은 Collector로 처리하고 잘못된 날짜 항목만 격리하도록 보완했다.
- C안 타일 기본·A안 클라우드 전환, 국가·날짜 선택, 상세 원문, 캐시 복구와 반응형 접근성 화면을 구현했다.
- 매일 16:00 JST/KST 실제 RSS를 검증·게시하는 Pages workflow와 실패 시 기존 배포 유지 구조를 구현했다.
- 출처·보관·개인정보·문의 페이지와 로컬 fixture preview 절차를 추가했다.
- 완료 리뷰 High 두 건인 Pages 출력 경로 보호와 보조 RSS 순위 가중치를 수정·재검증했다.
- PR #9 병합 후 GitHub Runner 임시 경로가 안전 검사에서 차단되어, 저장소 내부 `dist/site`를 Pages artifact 출력 경로로 사용하도록 병합 후 수정을 완료했다.

## 2주차 진행 결과

- 실제 provider를 주입할 수 있는 구조화 LLM client 경계와 결정적 mock extractor를 구현했다.
- 입력 기사 ID·근거 표현·국가 경계를 코드에서 검증해 환각과 국가 혼합을 차단한다.
- 국가 내부 유사 label을 병합하고 기사 수·매체 수·최신 시각·issue ID 순으로 TOP 5를 결정한다.
- 30초 timeout 전달, 최대 2회 재시도, 내용 hash cache, token·비용 기록과 월 USD 10 상한을 구현했다.
- 세 국가 pipeline, 국가별 실패 격리, 최소 2개국 게시, dry-run과 중복 실행 lock을 구현했다.
- 검증된 최근 7일 JSON을 기존 정상 site와 원자적으로 교체하는 static publisher를 구현했다.
- `StaticJsonDataSource`와 후속 `ApiDataSource`가 동일 Schema를 검증하도록 웹 기반을 추가했다.
- 마스킹된 로컬 장애 보고서와 fixture→검증된 정적 JSON 통합 CLI를 구현했다.

## 목표 2 진행 결과

- Pydantic v2 기반 이슈 결과 Schema와 국가·상태 enum을 구현했다.
- JSON Repository의 날짜별·최신 조회와 최근 날짜 검색을 구현했다.
- 세 국가 필수, timezone 포함 시각, HTTPS URL, 순위·비율·기사 수와 추가 필드 거부 규칙을 검증한다.
- 정상 조회, 파일 부재, 손상 JSON, 날짜 범위와 알 수 없는 파일 격리를 테스트했다.
- 날짜 결과와 `latest.json`의 원자적 저장, 오늘 포함 7일 보관·만료 삭제를 구현했다.
- `/api/v1` 전체 조회·상태·설정·health·ready endpoint와 400/404/503 오류 매핑을 구현했다.
- 목표 2 구현은 완료했으며 1주차 최종 커밋에는 목표 3 수집·정제까지 함께 포함한다.

## 목표 3 진행 결과

- 공통 Collector 계약 아래 JSON fixture adapter와 주입식 HTTPS RSS adapter를 구현했다.
- 추적 parameter 제거 URL, 정규화 제목, 6시간 내 0.92 이상 제목 유사도로 국가 내부 중복을 제거한다.
- US/JP/KR를 병렬 수집하고 한 국가·한 source 실패를 다른 국가 결과와 격리한다.
- `fixture`, `live`, `mixed` 실행 mode를 지원하며 mixed는 live 결과가 없을 때 fixture로 fallback한다.
- 익명화된 3개국 기사 fixture와 외부 network 호출 없는 통합 test를 추가했다.

## 완료된 목표

- 목표 1 — 환경과 프로젝트 골격
  - 완료일: 2026-08-03
  - PR: #5
  - `main` 커밋: `fb1fa04`
  - 검증: Ruff, mypy strict, pytest 4개, Secret 검사, fixture smoke, GitHub CI PASS

## 목표 1 진행 결과

- `backend`, `android`, `frontend`, `config`, `deploy`, `sample-data` monorepo 골격을 구성했다.
- Python 3.12, FastAPI, Pydantic Settings, uv 기반 backend 환경과 `uv.lock`을 구성했다.
- 기본 실행 모드를 `fixture`로 고정하고 외부 API·LLM key가 없어도 설정을 읽을 수 있게 했다.
- US/JP/KR가 독립된 샘플 fixture와 검증 테스트를 추가했다.
- PR과 `main`에서 공통 검증을 실행하는 기본 CI를 추가했다.
- 로컬 PATH에는 uv·Python·Java·ADB가 없었다. uv 0.11.32는 Git 제외된 `.tools/`에 설치해 검증했다. Java·Android SDK 설치는 보류하며 Android 재개 결정 후에만 필요하다.

## 현재 결정사항

- GitHub Pages MVP 기간은 2026-08-03부터 2026-08-22까지 3주다.
- 남은 개발은 주차마다 최종 커밋·브랜치·Draft PR을 하나씩 사용한다.
- 주차 리뷰는 토요일 고정 실행이 아니라 구현·테스트·문서·전체 검증 완료를 감지한 즉시 실행한다.
- 모든 커밋 제목은 `YYYY/MM/DD <type>: <English> | <한국어> | <日本語>` 형식을 사용한다.
- 현재 1차 결과물은 GitHub Pages URL의 반응형 웹이며 GitHub Actions가 생성한 정적 JSON을 `StaticJsonDataSource`로 읽는다.
- FastAPI와 `ApiDataSource`는 로컬 검증과 후속 VPS/EC2 전환을 위해 같은 Schema로 유지한다.
- Android는 삭제하지 않고 공개 웹 안정화 이후 선택적으로 재개하는 후속 트랙으로 보류한다. 재개 시 Retrofit을 우선 검토한다.
- Python 환경과 패키지는 uv로 관리한다.
- 한국어·일본어 명세는 같은 작업과 커밋에서 동기화한다.
- 메서드 단위 설명 주석은 일본어만 사용한다.

## 알려진 문제와 외부 의존성

- 운영 뉴스 소스 이용조건은 출시 전에 확인해야 한다.
- LLM 제공자와 실제 모델은 목표 4 시작 전에 환경변수 기반 어댑터로 확정한다.
- GitHub Pages 공개에는 VPS·EC2·별도 도메인 계약이 필요하지 않다.
- VPS/EC2와 도메인은 후속 API 운영을 선택할 때만 계약·연동한다.
- Google Play 계정과 Android SDK는 Android 후속 트랙을 재개하기 전까지 필요하지 않다.

## 목표 완료 시 갱신 항목

- 완료일과 커밋 SHA
- 구현 범위
- 실행한 검증 명령과 결과
- 남은 제한사항
- 다음 목표와 첫 작업
