# 개발 진행 상태

| 항목 | 현재 상태 |
|---|---|
| 현재 목표 | 국가 탭별 키워드 언어 전환 보정과 날짜 탭 정렬 |
| 상태 | 구현·문서·전체 검증·실제 공개 이력 preserve 검증·완료 리뷰 PASS, 게시 승인 대기 |
| 기준 브랜치 | `main` |
| 작업 브랜치 | `codex/keyword-language-tabs-fix` |
| 마지막 완료 커밋 | `de16f08e` — 키워드 한국어 표시 추가 |
| 전체 검증 | PASS — Python 159개·Web 14개, backend coverage 89%, Secret·명세·실제 preserve artifact |
| 다음 작업 | 사용자 요청 시 branch push와 Draft PR, 병합 후 `main` 재검증 |

## v1.0 공개 준비 진행 결과

- 2026-08-19 공개 데이터의 이전 Schema 2.0 JSON에 `label_ko`가 없어 국가 탭 이동 후 언어 전환이 원문 fallback으로만 보이던 원인을 확인했다. Pages `preserve` 게시도 현재 번역 사전으로 복원 이력을 보충해 외부 뉴스 API 재호출 없이 기존 날짜의 `label_ko`를 생성한다. 미국·일본 탭 간에는 선택한 언어 모드를 유지하고 한국 탭에서는 불필요한 전환 입력을 숨긴다. 날짜 탭은 왼쪽 과거·오른쪽 최신 순으로 정렬하고 선택 날짜를 가로 스크롤 영역에 노출한다. 실제 공개 이력 4일을 복원한 임시 artifact에서 US 2개·JP 3개가 한국어로 전환되고 모든 국가의 `label_ko` 누락이 0건임을 확인했다.

- 2026-08-19 미국·일본의 원문 키워드를 한국어 보조명으로 표시하는 `label_ko`를 Schema 2.0에 하위 호환 방식으로 추가했다. 순위 완료 후 version 관리되는 `config/keyword-translations.yml` 완전 일치 사전을 적용하며, 한국과 미등록 표현은 원문으로 fallback한다. Web 기본값은 한국어이고 `원문 / 한국어` segment가 타일·cloud·상세 title을 추가 network 요청 없이 함께 전환한다. 관련 기사 title은 원문을 유지하며 외부 번역 API·LLM 호출과 추가 비용은 없다. fixture, 이전 JSON 호환, 잘못된 label 거부와 실제 로컬 Pages 클릭 흐름을 검증했다.

- 2026-08-19 최근 실행을 분석해 Ubuntu gate와 Windows build 사이의 실행 marker cache 불일치, 09시 수집과 NewsData 무료 지연 충돌, 전체 국가 게시 gate, mutable JSON cache와 초기화 일괄 실패를 수정한다. marker는 Ubuntu gate에서 확인하고 교차 OS cache로 공유하며 Windows build의 전체 검증 후 외부 호출 직전에 저장하도록 바꾸고, 13시 기본·14시/16시 보충으로 변경했다. 1개국 이상 성공하면 국가별 부분 게시하고 `calendar.json`·`status.json`에서 실패 날짜·기사 수·사유를 제공하며, Web은 최신 데이터를 먼저 표시하고 상태 metadata 실패를 격리한다. 일반어·언론사명·정치인 필터, 영어 활용형, 최종 선택 수 기준 매체 편중, title embedding 응집도와 품질 3~5개 정책을 적용했다. 저장된 8월 17~19일 표본 재검증은 외부 API 호출 없이 수행했으며 무의미한 후보만 남은 미국 날짜는 미국만 실패하도록 확인했다.

- 2026-08-14 실제 24시간 표본의 후보 분산 문제를 수정한다. 복합어와 구성 단어를 함께 보존하고 local 다국어 SentenceTransformer의 고신뢰 의미 병합을 live 배치에 적용했다. 후보 gate를 2%·최소 3기사·2매체로 조정하고 의미 병합은 각 후보 2기사·2매체, 4자 이상, 유사도 0.95, cluster 최대 3개로 제한했다. 저장된 US 102·JP 70·KR 173건 재검증에서 세 국가 TOP 5가 생성됐으며 외부 뉴스 API와 LLM 호출은 사용하지 않았다.

- 코드 단순화 감사 결과에 따라 현재 운영 동작을 바꾸지 않는 범위에서 공통 사용량 장부와 정적 게시 helper를 도입하고, live collector 조립 중복과 Source YAML 반복 parse를 제거했다. Web 도구는 npm으로 통일하고 미사용 `public_issue_path`를 제거했다. v1·LLM·ApiDataSource는 명세상 후속 호환 경계이므로 사용자 결정 전까지 보존한다.

- GitHub 계정명을 `kimsb0430`으로 변경하고 저장소·Pages·문의·라이선스·RSS User-Agent·자동 보고 작업의 소유자 참조를 새 이름으로 통일한다. 기존 사용자명 리다이렉트에 의존하지 않는다.

- 2026-08-12 재실행은 원본 US 137·JP 128·KR 136건을 수집하고 중복 제거 후 US 133·JP 125·KR 132건을 확보했다. 매체 다양성 적용 후 최종 US 125·JP 55·KR 132건이 되었으며, 일본은 `Investing- Fx` 96건 집중으로 기존 70건 게시 하한에 미달했다. 권장 수집 100건 이상, 목표 150건과 매체별 20%/30건 제한은 유지하고 운영 변동 관찰을 위해 게시 하한만 당분간 50건으로 낮춘다. 50~99건 공개 결과는 국가별 기사 수와 TOP 5 품질을 매일 채팅으로 보고한다.

- 2026-08-12 예약 실행은 US 108·JP 40·KR 70건으로 일본이 70건 게시 하한에 미달했다. NewsData.io 무료 플랜의 12시간 지연을 소스별 수집 시간창에 반영하고 미국 15·일본 25페이지로 일 40회 예산을 배분했으며, 일본 요청에서 `investing.com`과 제공자 중복을 선제 제외한다. 한국 NAVER는 목표량이 남으면 5개 query의 두 번째 페이지까지 순회하고 승인 domain의 HTTP 링크를 HTTPS로 변환한다. 실응답을 확인한 JPX 2개·금융청 1개 공식 RSS를 일본 보조 소스로 추가했으며 매체별 20%/30건 제한은 유지한다.

- 운영 표본에서 경제 이슈와 무관한 정치인·정당명이 후보로 남는 문제에 대응해 국가별 YAML 금지 키워드 관리 기능을 추가했다. `config/keyword-blocklist.yml`의 `exact`·`contains` 규칙을 문서 빈도 계산 전에 적용하고, 최초 한국 규칙으로 `국힘`, `오세훈`을 등록했다. 설정 누락·Schema 오류·중복 규칙은 배치를 실패시켜 기존 정상 배포를 보존한다.

- PR #29 병합 후 `main` 로컬 전체 검증과 fixture/preserve smoke는 통과했으나 Pages `public-smoke`가 날짜별 JSON을 로컬로 받지 않은 채 강화된 artifact 검사를 실행해 실패했다.
- `dates.json`의 1~7개 안전한 날짜를 검증하고 모든 날짜 JSON을 받은 뒤 전체 계약을 검사하도록 수정했다. 현재 실제 공개 Pages smoke는 통과한다.
- `actions/deploy-pages`를 공식 Node.js 24 대응 v5.0.0 immutable SHA로 갱신해 남은 Node.js 20 경고를 제거한다.

- 2026-08-10 실제 실행의 US 139·JP 117·KR 72건 결과에서 실적·주가·이동평균, 날짜·출시, 억원·특징주 같은 반복 템플릿 일반어와 관련 기사 중복을 확인했다.
- 후보 기준을 최소 4건 또는 5%·2매체로 강화하고 날짜·단위·템플릿 일반어 제거, TOP5 관련 기사 Jaccard 중복 제거를 구현했다.
- NewsData.io 차단 매체와 일본 경제 제목 gate를 추가하고 반복 429의 GDELT를 일시 비활성화했으며 RSS XML 일시 오류는 1회 재파싱한다.
- live 실행은 최종 선택 기사 metadata와 수집 진단을 7일 관리자 artifact로 남기고, 공개 이력 직전 6일을 복원해 오늘 결과와 함께 최대 7일을 게시한다. `main` push는 fixture 대신 공개 데이터를 보존한다.
- GitHub Actions의 Node.js 20 경고 대상 action을 Node.js 24 호환 major로 갱신했다.

- 공개 Pages에서 세 국가 전환, TOP5, 타일·클라우드 전환, 상세 dialog와 관련 기사 20개 링크를 확인했고 console 오류가 없었다.
- 배포 성공·실패와 관계없이 현재 공개 HTML과 `data/v2` 계약을 확인하는 `public-smoke` job과 재시도 가능한 검사 스크립트를 추가했다.
- 예약·수동 재시도·배포·Secret 사고 대응과 7일 운영 게이트를 한·일 운영 런북 및 관찰표로 정리했다.
- 7일 연속 자동 배치 증거는 시간 경과가 필요한 출시 게이트로 계속 미완료 상태다.
- JST 날짜별 과거 24시간 계산과 수동 소급용 `--skip-rss --single-attempt`를 추가하고 8/2~8 실제 GDELT·NAVER 경로를 확인했다.
- 원본·중복 제거·최종 선택 건수와 소스별 기여도를 원문 없이 `data/runtime/collection-diagnostics.json`에 원자적으로 기록한다.
- 공식 무료 소스인 Census 경제지표 RSS와 BEA 뉴스 릴리스 RSS를 미국 보조 수집에 추가했다.
- 일본 재무성·통계국 공식 RSS를 추가하고 RSS 1.0/RDF 기본 namespace 파싱을 구현했다. 최근 168시간 제한 실연동에서 재무성 51건·통계국 5건을 수집했다.
- 대한민국 정책브리핑 RSS는 2026-07-01 중단 공지를 확인해 추가하지 않았다.
- GDELT·NAVER의 scope/domain/date/duplicate/limit 단계별 제외 건수와 NAVER 상위 제외 domain을 로컬 진단에 추가했다.
- NAVER 허용 domain `2026-08-08.v3` 제한 실연동에서 500건 중 103건을 채택했으며 진단용 별도 ledger는 25/300회다.
- GDELT 최소 요청에서 HTTP 429를 재현하고 안전한 오류 분류와 동일 배치 429 회로 차단기를 추가했다.
- NewsData.io 무료 Latest API를 미국·일본 `business` 보강 소스로 추가하고 국가별 목표·상한 150건, 일 40회·월 1,200회 hard stop과 유료 자동 전환 금지를 적용했다. 초기 최근 24시간 제한 실연동에서 US·JP 각각 100건을 확보했다.
- 첫 전체 live 게이트는 NewsData.io 원본 US/JP 각 100건에도 중복·매체 편중 적용 후 US 89·JP 73, NAVER KR 95로 안전하게 게시를 중단했다. 품질 기준은 유지하고 NewsData.io 목표를 150건으로 조정했으며 NAVER 허용 매체 v4를 근거 있는 주요 언론으로 보강했다. 일일 한도 보호를 위해 같은 날 추가 live 재시도는 하지 않는다.
- 다음 live 1회로 편중 원인을 확인할 수 있도록 진단 Schema 1.1에 소스별 채택 매체 집계를 추가했다. 기사 제목·URL·ID·Secret은 기록하지 않는다.
- PR #24 병합 후 Pages 운영 Secret이 주입된 검증에서 기본값 테스트가 환경변수를 격리하지 않아 실패한 원인을 확인했다. post-merge fix에서 credential 환경변수 격리와 Linux 공개 smoke 임시 경로 호환성을 수정한다.
- 실제 live 수집은 US 108·JP 129·KR 107건을 확보했지만 일본어 조사 분리 후 한 글자 후보가 Schema 검증 예외를 일으켜 게시가 중단됐다. 한 글자 조각을 후보 없음으로 처리하는 회귀 수정 후 다시 게시한다.
- PR #26 병합 후 실제 live 배포에서 US 114·JP 124·KR 103건과 세 국가 TOP 5 게시에 성공했다. 다만 제목 앞 3단어가 문장 조각으로 노출되는 품질 문제를 확인해, `kiwipiepy`·`SudachiPy`와 영어 단어 정규화 기반의 하나의 짧은 이슈 개념 추출로 교체한다.
- 7개 날짜 모두 세 국가 100건에 미달해 게시가 안전하게 차단됐다. 최대치는 8/3 US 34·KR 90, 8/5 JP 26·KR 90이며 NAVER는 40/300회를 사용했다.
- 2026-08-09 예약 실행은 중복·편중 제거 후 US 198·JP 103·KR 85건을 확보했지만 기존 100건 게시 게이트로 배포하지 않았다. 권장 수집 목표 100건 이상과 목표치 150건은 유지하고 실제 게시 하한만 국가별 70건으로 조정한다.

## 키워드 뉴스 v2 결정

- Schema 2.0, `/api/v2/keywords`, `data/v2`와 v1 독립 Repository를 추가해 v1 계약을 보존했다.
- 웹 기본 DataSource를 v2로 전환하고 국가별 TOP 5 클릭 시 관련 기사 최대 20건을 표시한다.
- main push는 국가별 120건 fixture TOP 5를 배포하고, 예약 실행은 직전 24시간 GDELT·RSS·NAVER 결과가 기준을 통과할 때만 기존 정상 Pages를 교체한다.

- 언어별 결정적 복합명사 후보 추출, 국가별 일반어·서술어 제거와 입력 후보 한정 동의어 통합을 구현했다.
- 국가별 게시 하한 70건을 강제하고 문서 빈도·매체 다양성·최신 시각·ID로 TOP 5를 결정하며 관련 기사 ID를 최대 20건 연결한다.
- 국가별 120건 fixture에서 기대 복합명사 5개, 결정성, 일반어 제외, 국가 분리와 원문 근거 연결을 검증한다.

- GDELT DOC API를 국가별 주 소스로, 기존 공공 RSS/API를 보조 소스로 전환한다.
- 중복 제거 후 국가별 150건을 목표로 하고 최대 250건, 권장 수집 100건 이상, 게시 가능 70건 이상, 부분 성공 50~69건으로 정한다.
- 언어별 명사·복합명사 추출과 불용어 제거 후 LLM은 동의어·표시명 통합만 수행한다.
- 문서 빈도와 매체 다양성으로 키워드 TOP 5를 정하고 키워드별 관련 기사 최대 20개를 제공한다.
- 기존 v1 의미를 보존하고 Schema/API/정적 JSON을 v2로 함께 전환한다.
- 상세 근거와 구현 순서는 `docs/adr/ADR-0001-keyword-news-pipeline.md`를 따른다.
- 1차 운영은 GDELT·NAVER 무료 한도·공식 RSS/API만 사용하며 유료 뉴스 API와 외부 유료 LLM 자격정보는 등록하지 않는다.
- GDELT와 공식 RSS에는 Secret이 필요 없고, 한국 뉴스 보강 시에만 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`이 필요하다.
- NAVER 사용 정책은 일 300회·월 9,000회 hard stop, 50%·80% 알림, 유료 초과 사용 비활성으로 확정했으며 코드 설정과 차단 가드를 추가했다. 계정 전체 차단과 알림은 Console에서 같은 값으로 설정해야 한다.
- NAVER 뉴스 수집 adapter, 한국 경제 검색어 순환, 승인 언론사 원문 domain filter, 인증 header, HTML title 정리와 영속 사용량 ledger를 구현했다. v1 보호를 위해 `--enable-naver` 명시 실행에서만 활성화한다.
- NAVER 제한 실연동은 `경제` 1회에서 승인 domain 5곳·6건, 5개 query에서 승인 domain 7곳·중복 제거 31건을 확보했다. NAVER 단독 100건에는 미달하므로 GDELT·RSS 합산과 근거 있는 query·allowlist 보강이 필요하다.
- 완료 리뷰 High에서 무료 정책 재검토일 이후에도 호출 가능한 위험을 발견해, 재검토 기한 만료 시 인증 요청 전에 자동 중단하도록 수정했다.
- GDELT JSON adapter, query version, 국가별 120건 fixture, 250건 상한과 매체별 20%/30건 제한을 구현했다.
- 제한적 live 검증은 무료 endpoint 429와 실제 매체 coverage로 US 43건·JP/KR 오류가 발생해 원인 있는 partial로 기록했다. 앞선 호출에서는 KR 원본 250건·4매체를 확인했다.
- 기존 v1 Pages를 보호하기 위해 `publish-live --enable-gdelt`를 명시한 평가에서만 GDELT를 사용하고 v2 전환 전 예약 배치는 RSS를 유지한다.

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
- 매일 09:00 JST/KST 실제 RSS를 검증·게시하는 Pages workflow와 실패 시 기존 배포 유지 구조를 구현했다.
- 10:00·12:00 JST/KST 보충 schedule과 날짜별 live-attempt cache marker를 추가했다. 외부 수집 단계에 진입한 날은 성공·실패와 무관하게 자동 live 재실행을 차단하고, 수집 전 단계 실패만 보충한다.
- 병합 push가 부족한 live RSS를 실행해 빌드에 실패하고 당일 시도권을 소비하던 문제를 수정했다. `main` push는 fixture를 배포하고 예약·명시적 수동 실행만 live mode를 사용한다.
- 출처·보관·개인정보·문의 페이지와 로컬 fixture preview 절차를 추가했다.
- 완료 리뷰 High 두 건인 Pages 출력 경로 보호와 보조 RSS 순위 가중치를 수정·재검증했다.
- PR #9 병합 후 GitHub Runner 임시 경로가 안전 검사에서 차단되어, 저장소 내부 `dist/site`를 Pages artifact 출력 경로로 사용하도록 병합 후 수정을 완료했다.
- 공개 화면의 초기 데이터 로딩 실패 상태에서 국가 버튼이 null 결과를 렌더링하던 문제를 방어하고 재시도 UI와 DOM 동작 테스트를 추가했다.
- PR #11 최초 CI에서 `jsdom` 의존성 미설치를 확인해 기본 CI에 Node.js와 `npm ci` 단계를 추가했다.
- 실제 브라우저의 `window.fetch` 호출 컨텍스트를 보존하고 favicon 404를 제거하는 병합 후 수정을 진행한다.
- 확정 앱 샘플의 흰색·블루 시각 체계와 정보 구조를 반응형 웹에 적용한다.
- `deploy-pages`가 설정값과 무관하게 10분으로 제한됨을 실행 로그에서 확인해 deploy job을 10분으로 복구하고, 대기열 timeout 후 지연 수동 재시도 1회 정책으로 정정한다.
- PR #15의 새 `main` SHA 배포도 10분 동안 `deployment_queued` 후 취소됐고, 같은 SHA의 수동 재실행은 즉시 `Deployment cancelled`로 종료됐다. 취소된 Pages 배포 ID를 반복 사용하지 않도록 문서 변경을 새 SHA로 병합해 한 번 재배포한다.

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
