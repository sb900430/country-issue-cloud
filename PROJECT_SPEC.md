# 국가별 이슈 클라우드 (Country Issue Cloud)

> 미국·일본·한국의 경제뉴스를 국가별로 독립 분석하고, 각 국가가 그날 주목한 경제 이슈를 URL로 확인하는 반응형 웹 애플리케이션

## 문서 정보

| 항목 | 내용 |
|---|---|
| 목적 | 기획·설계·개발·테스트·배포·운영의 단일 기준 |
| 프로젝트명 | 국가별 이슈 클라우드 |
| 영문명 | Country Issue Cloud |
| 서비스 이름 | 이슈 클라우드 |
| 저장소명 | `country-issue-cloud` |
| 기준 시간대 | `Asia/Tokyo` |

중요한 설계 변경은 이 문서와 코드에 함께 반영하고 `docs/adr/`에 ADR로 남긴다. 이 문서의 일본어판은 `PROJECT_SPEC_JA.md`이며 두 파일은 동일한 명세를 담는 동등한 기준 문서다. 관련 내용을 변경할 때는 한국어판과 일본어판을 같은 작업과 커밋에서 함께 수정한다.

---

## 1. 프로젝트 개요

매일 미국·일본·한국의 경제뉴스를 국가별로 독립 수집한다. 각 국가 안에서 의미가 유사한 기사와 표현을 하나의 이슈로 묶고, 고유 기사 수와 매체 다양성을 기준으로 국가별 TOP 5를 계산한다. 사용자는 같은 날짜에 각 나라가 무엇을 중요하게 다뤘는지 국가 탭을 전환하며 확인한다.

이 프로젝트는 다음 목적을 가진 비상업적 포트폴리오다.

1. 모바일과 PC에서 URL로 접속할 수 있는 반응형 웹 서비스를 제작·배포한다.
2. GitHub에 설계, 개발, 테스트, 배포 이력을 공개한다.
3. 매일 데이터가 갱신되는 서비스를 실제 운영한다.
4. 다국어 처리, LLM 구조화 출력, 배치/API 분리, 웹 접근성·캐시, CI/CD 역량을 증명한다.

Android 앱은 폐기하지 않는다. 웹 MVP와 공개 URL의 안정화가 끝난 뒤 동일한 `/api/v1` 계약을 사용하는 후속 선택 트랙으로 보류한다. 현재 로컬 MVP와 1차 공개 범위에는 Android 구현·Google Play 배포를 포함하지 않는다.

### 사용자 가치

- 같은 날짜의 세 나라 경제 관심사를 빠르게 비교한다.
- 단순 단어 빈도가 아니라 유사 표현을 묶은 의미 있는 이슈를 본다.
- 기사 수, 매체 수, 대표 출처로 선정 근거를 확인한다.
- 오프라인에서도 마지막 정상 결과를 확인한다.

### 하지 않는 것

- 세 국가 공통 키워드의 교집합을 계산하지 않는다.
- 한 국가 키워드를 세 언어로 번역해 공통 결과처럼 표시하지 않는다.
- LLM이 최종 순위를 임의로 결정하지 않는다.
- 기사 원문 전체를 저장·재배포하지 않는다.
- 비공식 HTML 스크래핑을 사용하지 않는다.
- 투자 추천이나 금융 자문을 제공하지 않는다.

---

## 2. 성공 기준과 범위

### 성공 기준

- GitHub Pages의 반응형 웹 페이지와 게시 JSON이 하나의 HTTPS URL로 외부에서 접근 가능하다.
- 최소 2개국 결과가 매일 자동 갱신된다.
- 최근 7일의 국가별 TOP 5와 근거 기사를 확인할 수 있다.
- 브라우저 캐시로 마지막 정상 데이터를 볼 수 있다.

| 지표 | 목표 |
|---|---:|
| 최근 30일 배치 게시 성공률 | 95% 이상 |
| Pages·게시 JSON 가용성 내부 목표 | 99% 이상 |
| 정적 JSON 응답시간 목표 | 500ms 이내 |
| 마지막 정상 데이터 | 48시간 이내 |
| 국가별 정상 권장 표본 | 30개 이상 |
| 국가별 게시 가능 표본 | 15개 이상 |
| 이슈 추출 성공률 | 80% 이상 |

### 1차 출시 포함

- 국가별 수집, 정제, 중복 제거, 이슈 클러스터링, TOP 5
- 최근 7일 JSON 게시, 로컬·후속용 FastAPI와 공통 Schema
- 반응형 웹 타일/클라우드, 상세, 브라우저 캐시
- 부분 성공, 지연, 점검, 오류 상태
- 모바일·데스크톱 정식 웹 UI
- 자동 리뷰와 Markdown 장애 보고서
- GitHub Actions 예약 배치·검증·Pages 배포, GitHub Pages HTTPS

### 1차 제외

- 로그인, 댓글, 광고, 결제, 개인화 추천
- 서버 동기화 즐겨찾기, 푸시 알림
- VPS·EC2 운영 배포, Android·iOS 네이티브 앱, Google Play 배포, 7일 초과 이력, 실시간 스트리밍

---

## 3. 핵심 원칙

```text
미국 경제뉴스 전체 → 미국 이슈 TOP 5
일본 경제뉴스 전체 → 일본 이슈 TOP 5
한국 경제뉴스 전체 → 한국 이슈 TOP 5
```

- 특정 공통 주제를 먼저 정해 세 국가에서 검색하지 않는다.
- 한 국가 실패는 다른 국가의 처리와 표시를 막지 않는다.
- 이슈명은 원어를 기준으로 하고 미국·일본에는 한국어 보조명을 둘 수 있다.
- 보조 번역은 집계와 순위에 사용하지 않는다.
- 기사에 없는 표현을 근거로 생성하지 않는다.
- LLM은 추출과 클러스터링만 담당한다.
- 순위는 고유 기사 수, 고유 매체 수, 최신 시각, `issue_id` 순으로 코드가 계산한다.
- 공식 API 또는 공개 RSS만 사용하고 원문 전체와 이미지는 저장하지 않는다.
- API와 배치는 서로의 실행 모듈을 import하지 않고 게시 JSON으로만 통신한다.
- 결과는 임시 작성, Schema 검증, 원자적 교체 순으로 게시한다.

---

## 4. 기능 요구사항

| ID | 기능 | 설명 |
|---|---|---|
| F-01 | 국가별 수집 | 국가별 최대 100개 경제뉴스 독립 수집 |
| F-02 | 정제·중복 제거 | URL, 제목, 유사도로 국가 내부 중복 제거 |
| F-03 | 이슈 추출 | LLM으로 경제 이슈 후보 추출 |
| F-04 | 클러스터링 | 국가 내부 유사 표현과 기사 병합 |
| F-05 | TOP 5 | 기사 수와 매체 수로 순위 산출 |
| F-06 | 결과 저장 | 날짜 JSON과 latest 원자적 저장 |
| F-07 | 품질 리뷰 | 표본, 편중, 추출률, 라벨 점검 |
| F-08 | 장애 보고서 | 원인, 영향, 개선안, 스택 기록 |
| F-09 | 보관 | 결과 7일, 보고서 90일, 로그 30일 |
| F-10 | 정기 실행 | GitHub Actions schedule과 제한 재시도, 후속 systemd timer 호환 |
| F-11 | 날짜 조회 | 최근 7일 조회 가능 날짜 제공 |
| F-12 | 국가 전환 | 같은 날짜의 국가별 결과 즉시 전환 |
| F-13 | 이슈 시각화 | TOP 5를 기본 타일형 또는 클라우드형으로 전환 표시 |
| F-14 | 상세 | 통계, 대표 기사, 원문 링크 |
| F-15 | 오프라인 | 브라우저 캐시로 마지막 정상 결과 표시 |
| F-16 | 서비스 설정 | 점검, 버전, 공지, 정책 URL |
| F-17 | 상태 | 최신 데이터와 국가 상태 제공 |

---

## 5. 수집 정책

- 서비스 시간대: `Asia/Tokyo`
- 배치: 매일 08:00
- 수집 범위: 실행 시각 기준 직전 24시간
- 내부 시간: UTC, 표시: 타임존 포함 ISO 8601
- 발행 시각이 없거나 현재보다 10분 이상 미래인 기사는 제외한다.

| 구분 | 기준 |
|---|---:|
| 국가별 목표 | 최대 100개 |
| 정상 권장량 | 30개 이상 |
| 게시 최소량 | 15개 이상 |
| 단일 매체 최대 반영 | 20개 권장 |
| 매체 편중 경고 | 40% 초과 |
| 심각한 편중 | 60% 초과 |

정확히 100개보다 적법성과 투명성을 우선하며 실제 기사 수를 앱에 표시한다.

### 출처 정책

- NewsAPI 무료 플랜은 로컬 개발·테스트에서만 사용한다.
- 운영은 공식 RSS 또는 운영 사용이 허용된 공개 API만 사용한다.
- 국가별 최소 2개 출처를 목표로 한다.
- 일일 공식 발표량을 고려해 국가별 5건 이상은 부분 성공, 15건 이상은 완전 성공의 수집 기준으로 사용한다.
- 등록 소스는 공식 RSS·공공 API만 사용하며 민간 뉴스 HTML과 정책브리핑의 중단된 RSS는 사용하지 않는다.
- 소스별 이용조건 확인일과 허용 필드를 설정에 기록한다.
- 이용조건은 90일마다 재확인하고 승인·등록·앱 ID가 필요한 소스는 확인 전 비활성으로 둔다.

```yaml
US: Federal Reserve RSS; BLS RSS는 자동 요청 403으로 비활성, BEA API는 등록 후 활성화
JP: BOJ RSS; METI Atom은 갱신 중단으로 비활성, e-Stat API는 app ID 등록 후 활성화
KR: 한국은행 RSS, 금융위원회 보도자료·보도설명 RSS, 중소벤처기업부 보도자료 RSS
```

기본 허용 필드는 RSS가 직접 제공한 제목·짧은 요약·원문 URL·매체·발행 시각이다. BOJ·BOK·금융위원회·중소벤처기업부는 보수적으로 제목·URL·매체·발행 시각만 사용한다. 금융위원회 보도설명 RSS는 일반 보도자료를 보완하는 보조 소스로 사용한다. 기사 본문, PDF·첨부파일, 이미지와 HTML을 파싱한 요약은 수집·재배포하지 않는다. 실제 URL과 승인 상태는 `config/sources.example.yml`을 기준으로 하며, 조건부 비활성 소스의 등록·승인·Secret·검증 절차는 `docs/SOURCE_REGISTRATION_GUIDE.md`를 따른다.

### 중복 제거

1. 추적 파라미터를 제거한 URL 일치
2. HTML·공백·문장부호·대소문자를 정규화한 제목 일치
3. 제목 유사도 0.92 이상, 발행 시각 차이 6시간 이내

대표 기사는 제목·요약 존재, 유효 시각, HTTPS 링크, 이른 발행 시각 순으로 선택한다.

---

## 6. LLM과 집계

LLM은 번역 워드클라우드를 만드는 도구가 아니라 한 국가 안의 유사 사건을 의미 단위로 묶는 도구다.

```text
기준금리 동결 / 금통위 금리 결정 / 한국은행 통화정책
→ 기준금리 동결
```

LLM은 이슈 후보, 국가 내부 클러스터, 원어 라벨, 한국어 보조명, 구조화 JSON을 생성한다. 국가 간 병합, 순위 결정, 투자 판단은 하지 않는다.

```json
{
  "country": "KR",
  "issues": [{
    "issue_label": "기준금리 동결",
    "display_label_ko": "기준금리 동결",
    "article_ids": ["kr-001", "kr-014"],
    "evidence_expressions": ["기준금리 동결", "금통위 금리 결정"]
  }]
}
```

- JSON Schema/Pydantic 검증
- 입력에 존재하는 기사 ID와 근거 표현만 허용
- 모델/프롬프트 버전 기록, 가능한 경우 temperature 0
- 기사 10~20개 묶음 처리와 내용 해시 캐시
- timeout 30초, 재시도 최대 2회
- 월 USD 10 상한, USD 5 상당에서 경고

```text
article_count   = 이슈 고유 기사 수
publisher_count = 이슈 고유 매체 수
article_ratio   = 이슈 기사 수 / 국가 유효 기사 수
```

`success`: 기사 30개 이상, LLM 성공률 80% 이상, 이슈 3개 이상.

`partial_success`: 기사 15개 이상, LLM 성공률 70% 이상, 이슈 1개 이상.

최소 2개국이 게시 가능할 때 날짜 결과를 저장하며 실패 실행은 `latest.json`을 바꾸지 않는다.

---

## 7. 데이터 스키마와 보관

```json
{
  "schema_version": "1.0",
  "date": "2026-07-29",
  "generated_at": "2026-07-29T08:10:00+09:00",
  "status": "success",
  "countries": {
    "US": {
      "status": "success",
      "article_count": 72,
      "extraction_success_rate": 0.95,
      "top_issues": [{
        "rank": 1,
        "issue_id": "us_fed_rate_outlook",
        "issue_label": "Fed interest rate outlook",
        "display_label_ko": "연준 기준금리 전망",
        "article_count": 18,
        "publisher_count": 8,
        "article_ratio": 0.25,
        "representative_articles": [{
          "title": "Example title",
          "publisher": "Example Publisher",
          "published_at": "2026-07-28T21:20:00Z",
          "url": "https://example.com/article"
        }]
      }],
      "warnings": []
    },
    "JP": {},
    "KR": {}
  }
}
```

```text
data/
├── published/
│   ├── issues_2026-07-29.json
│   └── latest.json
├── cache/
├── temp/
└── runtime/pipeline.lock

reports/
└── incident_2026-07-29T081000_collect_JP.md
```

| 데이터 | 보관 기간 |
|---|---:|
| 날짜별 결과 | 오늘 포함 7일 |
| `latest.json` | 최신 1개 |
| 성공 임시 데이터 | 배치 후 즉시 삭제 |
| 실패 임시 데이터 | 24시간 |
| 장애 보고서/실행 요약 | 90일 |
| 애플리케이션 로그 | 30일 |

---

## 8. API 설계

논리적 API 계약의 기본 경로는 `/api/v1`이다. 로컬과 후속 VPS/EC2에서는 FastAPI endpoint로 제공하고, GitHub Pages 1차 운영에서는 같은 응답 Schema를 `data/v1/.../*.json` 정적 경로로 게시한다. 웹 UI는 경로를 직접 참조하지 않고 DataSource 인터페이스를 사용한다.

| Method | Path | 설명 |
|---|---|---|
| GET | `/issues/latest` | 마지막 게시 결과 |
| GET | `/issues/dates` | 최근 7일 사용 가능 날짜 |
| GET | `/issues/{date}` | 한 날짜의 세 국가 결과 |
| GET | `/issues/{date}/{country}` | 특정 날짜·국가 결과 |
| GET | `/status` | 데이터 최신성과 국가 상태 |
| GET | `/app-config` | 점검·버전·공지·정책 URL |
| GET | `/health` | 프로세스 생존 확인 |
| GET | `/ready` | 저장소 포함 준비 상태 |

| HTTP | 오류 코드 | 조건 |
|---:|---|---|
| 400 | `invalid_date` | 날짜 형식 오류 |
| 400 | `date_out_of_range` | 최근 7일 범위 밖 |
| 400 | `invalid_country` | US/JP/KR 외 값 |
| 404 | `issue_not_found` | 날짜 결과 없음 |
| 404 | `country_not_available` | 국가 결과 없음 |
| 503 | `service_maintenance` | 점검 상태 |
| 500 | `internal_error` | 서버 내부 오류 |

- 오류 응답에는 `request_id`만 제공하고 내부 상세를 숨긴다.
- `ETag`, `Last-Modified`, `Cache-Control`을 지원한다.
- 출시된 v1 필드를 삭제하거나 의미를 변경하지 않는다.
- 앱에는 뉴스 API와 LLM 비밀키를 넣지 않는다.
- Pages 모드에서는 정적 JSON만 읽고 외부 서비스 키를 브라우저에 노출하지 않는다.
- VPS/EC2 API 모드에서는 nginx 또는 동등한 gateway rate limit을 적용한다.

---

## 9. 웹 UI 설계와 Android 보류

| 구분 | 선택 |
|---|---|
| 언어/UI | Semantic HTML, CSS, Vanilla JavaScript |
| 구조 | UI → 상태/서비스 모듈 → IssueDataSource → 브라우저 캐시 |
| 네트워크 | 기본 `StaticJsonDataSource`, 후속 `ApiDataSource` |
| 저장 | localStorage(보기 설정), Cache API 또는 IndexedDB(최근 정상 응답) |
| 지원 환경 | 최신 Chrome, Edge, Safari, Firefox의 모바일·데스크톱 |
| 1차 배포 | GitHub Pages가 정적 웹과 생성된 JSON을 같은 HTTPS origin에서 제공 |
| 후속 배포 | 설정으로 VPS/EC2 FastAPI `/api/v1`을 선택하고 필요 시 CORS 적용 |
| Android | 공개 웹 안정화 이후 재검토하는 보류 트랙 |

### 코드 주석 언어

- 메서드·함수 단위의 설명 주석과 KDoc/docstring은 일본어로만 작성한다.
- 메서드의 목적, 매개변수, 반환값, 예외, 중요한 전제조건을 설명할 필요가 있을 때 일본어를 사용한다.
- 자명한 코드에는 주석을 억지로 추가하지 않고, 구현 자체가 의도를 드러내도록 이름을 명확히 짓는다.
- TODO/FIXME도 설명 문장은 일본어로 작성한다. 라이브러리명, API명, 코드 식별자와 공식 오류 메시지는 원문 표기를 유지할 수 있다.
- 이 규칙은 Kotlin, Python, JavaScript와 이후 추가되는 모든 소스 코드에 동일하게 적용한다.

### 화면

1. 초기 로딩
2. 이슈 클라우드 홈
3. 이슈 상세와 대표 기사
4. 프로젝트 정보
5. 개인정보처리방침/문의
6. 오픈소스 라이선스
7. 점검/업데이트 안내

홈 화면은 앱 제목/기준일, 국가 탭, 최근 7일, `오늘의 이슈 TOP 5` 시각화, 마지막 업데이트 시각과 새로고침 순이다. 국가 탭은 같은 날짜 응답을 사용해 추가 요청 없이 전환하고 날짜 변경 때만 요청한다.

### 홈 화면 UI 확정안

홈 화면의 TOP 5는 하나의 시각화 영역에서만 제공한다. 같은 다섯 개 이슈를 하단 목록으로 다시 표시하지 않는다.

| 항목 | 확정 동작 |
|---|---|
| 기본 보기 | 가중치 타일형(C안) |
| 대체 보기 | 자유형 이슈 클라우드(A안) |
| 전환 방식 | 시각화 영역 오른쪽 위의 `타일 / 클라우드` 슬라이드형 세그먼트 버튼 |
| 상태 저장 | 최초 접속은 타일형, 이후에는 localStorage에 마지막 선택을 저장하고 재접속 시 복원 |
| 공통 제목 | `오늘의 이슈 TOP 5` |
| 공통 정보 | 분석 기사 수와 데이터 생성/업데이트 시각 |
| 하단 영역 | 마지막 업데이트 시각과 새로고침 버튼만 표시 |
| 상세 진입 | 타일 또는 클라우드 키워드를 누르면 동일한 이슈 상세 화면으로 이동 |

타일형은 순위, 이슈명, 기사 수를 각 타일에 표시한다. 1위 타일을 가장 크게 표현하고 나머지는 중요도에 따라 크기와 명도를 조절한다. 타일 전체를 터치 영역으로 사용한다.

클라우드형은 같은 TOP 5를 가로쓰기 텍스트로 배치하고 `article_ratio`에 따라 글자 크기와 명도를 조절한다. 텍스트를 회전하거나 겹치지 않으며, `키워드를 누르면 관련 기사를 볼 수 있어요` 안내를 표시한다. 순위와 정확한 기사 수는 키워드 접근성 설명과 상세 화면에서 확인할 수 있게 한다.

보기 전환은 데이터 재요청이나 재집계를 발생시키지 않고 동일한 웹 상태를 다른 DOM 컴포넌트로 렌더링한다. 국가·날짜·로딩·오류 상태와 스크롤 위치는 전환 과정에서 유지한다.

권장 웹 컴포넌트 구조:

```text
IssueHomePage
├── CountryTabs
├── RecentDateSelector
├── IssueSectionHeader
│   ├── ArticleSummary
│   └── IssueViewModeToggle
├── IssueVisualization
│   ├── WeightedIssueTiles     // 기본 C안
│   └── DeterministicIssueCloud // 전환 A안
└── UpdateFooter
    ├── LastUpdatedText
    └── RefreshButton
```

### Android 후속 보류 트랙

- `android/` 디렉터리와 Android 설계 기록은 삭제하지 않고 보류 상태로 유지한다.
- 현재 웹 MVP에서는 Android 구현, SDK 설치, Emulator 검증, AAB 생성, Google Play 제출을 완료 조건으로 삼지 않는다.
- 공개 URL과 웹 API가 안정화된 뒤 사용자가 재개를 결정하면 동일한 `/api/v1` 계약과 UI 동작을 재사용한다.
- 재개 시점에 Kotlin, Compose, Retrofit, Room, DataStore 후보를 다시 검증하고 별도 ADR·일정·비용·Play 정책을 확정한다.

### 클라우드 규칙

- 국가별 `article_ratio`로 글자 크기를 계산한다.
- 최소/최대 크기를 제한하고 순위 기반 결정적 배치를 사용한다.
- 무작위 회전, 과도한 색상, 색상만으로 구분하는 방식을 피한다.
- 포인트 컬러 하나와 명도 차이만 사용한다.
- 긴 라벨은 최대 두 줄, 선택하면 상세 화면으로 이동한다.

### 상태

| 상태 | 처리 |
|---|---|
| 정상 | 선택된 방식으로 TOP 5 시각화 표시 |
| 로딩 | 스켈레톤과 국가·날짜·보기 입력 제한 |
| 오늘 미준비 | 최신 날짜 폴백과 안내 |
| 부분 성공 | 해당 국가에 제한 안내 |
| 국가 실패 | 해당 국가만 갱신 지연 표시 |
| 오프라인+캐시 | 캐시와 마지막 확인 시각 |
| 오프라인+캐시 없음 | 원인 기록, 연결 안내와 재시도 버튼; 결과가 없으면 렌더링하지 않음 |
| 서버 오류 | 기존 캐시 유지 |
| 점검 | 서버 제공 점검 문구 |
| 오래된 앱 | 선택/필수 업데이트 안내 |

Room을 읽기 기준 데이터로 사용하며 유효한 서버 응답만 저장한다. 최근 7일만 보관하고 선택 국가/날짜를 프로세스 재생성 후 복원한다. TalkBack, 글자 확대, 최소 터치 영역, 명암비, 태블릿/폴더블, 다국어 글리프를 검증한다.

---

## 10. 백엔드와 프로젝트 구조

```text
country-issue-cloud/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/v1/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   │   ├── base.py
│   │   │   └── json_issue_repository.py
│   │   ├── models/
│   │   └── batch/
│   │       ├── collectors/
│   │       ├── deduplicator.py
│   │       ├── issue_extractor.py
│   │       ├── clusterer.py
│   │       ├── aggregator.py
│   │       ├── review.py
│   │       ├── incident_report.py
│   │       └── pipeline_entry.py
│   └── tests/
├── android/
├── frontend/
│   ├── src/data/
│   │   ├── issue-data-source.js
│   │   ├── static-json-data-source.js
│   │   └── api-data-source.js
│   └── public/data/v1/
├── config/
├── deploy/
├── docs/
│   ├── architecture.md
│   ├── AI_DEVELOPMENT_GUIDE.md
│   ├── AI_DEVELOPMENT_GUIDE_JA.md
│   ├── DEVELOPMENT_STATUS.md
│   ├── DEVELOPMENT_STATUS_JA.md
│   ├── daily/
│   │   ├── TEMPLATE.md
│   │   └── YYYY-MM-DD.md
│   ├── functional-design.md
│   ├── screen-design.md
│   ├── api-spec.md
│   ├── data-policy.md
│   ├── deployment-guide.md
│   ├── operations-runbook.md
│   ├── review/
│   │   ├── WEEKLY_REVIEW_GUIDE.md
│   │   └── WEEKLY_REVIEW_TEMPLATE.md
│   └── adr/
├── sample-data/
├── scripts/
│   ├── check-spec-sync.ps1
│   └── verify-all.ps1
├── .github/workflows/
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .env.example
└── README.md
```

Repository 최소 계약:

```python
find_by_date(date)
find_latest()
find_available_dates(within_days)
save(result)
delete_expired(retention_days)
```

JSON을 SQLite/PostgreSQL로 바꿔도 Router, Service, 웹 API 계약과 보류된 Android API 계약은 유지한다.

정식 웹 UI는 정적 HTML/CSS/Vanilla JS로 만들고 DataSource에 관계없이 같은 응답 Schema와 상태 정의를 사용한다. 기본 설정은 `DATA_MODE=static`, `DATA_BASE_URL=./data/v1`이며 후속 서버에서는 `DATA_MODE=api`, `API_BASE_URL=https://.../api/v1`로 교체한다. 모바일 우선 반응형 레이아웃, 포인트 컬러 하나, 단순한 클라우드 디자인을 적용한다. 생성된 운영 JSON은 Pages 배포 artifact에는 포함하지만 소스 브랜치에는 커밋하지 않는다.

---

## 11. 배치와 스케줄링

```text
1. OS lock 획득
2. 설정과 소스 확인
3. US/JP/KR 병렬 수집
4. 국가별 정제·중복 제거
5. 국가별 LLM 이슈 추출
6. 국가별 클러스터링
7. 국가별 TOP 5 집계
8. 품질 리뷰
9. 게시 조건 판정
10. 임시 JSON 작성·검증
11. 날짜 파일 원자적 교체
12. latest.json 갱신
13. 만료 데이터 삭제
14. 실행 요약과 lock 해제
```

| 시각 | 작업 |
|---|---|
| 08:00 | 기본 배치 |
| 08:30 | 결과가 없을 때 1차 재시도 |
| 09:30 | 여전히 없을 때 마지막 재시도 |
| 10:00 | 상태 점검과 연속 실패 알림 후보 |

1차 운영은 GitHub Actions의 JST timezone schedule로 실행하고 workflow concurrency로 중복 실행을 막는다. 예약 실행은 지연될 수 있으므로 정각 의존 로직을 두지 않고 수동 `workflow_dispatch` 복구 경로를 제공한다. 공개 저장소의 장기 비활동으로 schedule이 중단될 가능성을 운영 점검에 포함한다. 후속 VPS/EC2에서는 동일한 pipeline entry를 systemd timer의 `Persistent=true`와 OS 파일 잠금으로 실행한다. 두 모드 모두 이미 게시된 날짜는 기본적으로 건너뛴다.

```text
python -m app.batch.pipeline_entry
python -m app.batch.pipeline_entry --date 2026-07-29
python -m app.batch.pipeline_entry --dry-run
python -m app.batch.pipeline_entry --force
python -m app.batch.pipeline_entry --countries US,JP
```

- `--dry-run`: 게시 파일을 바꾸지 않는다.
- `--force`: 새 결과 검증 성공 시에만 교체한다.
- lock 획득 실패는 `skipped_locked`로 기록한다.

장애 보고서에는 실행 ID, 실패 국가/단계, 예외, 원인 분류, 영향, 재시도, 개선안 3개, 마스킹한 스택 트레이스를 기록한다. 한 국가 실패와 만료 삭제 실패는 가능한 경우 전체를 중단하지 않는다.

---

## 12. 보안·개인정보·웹 배포와 Android 보류

### 앱과 서버

- 로그인, 광고, 위치·연락처·사진·저장소 권한을 사용하지 않는다.
- 웹은 기기 권한을 요구하지 않으며 CSP, HTTPS, 안전한 외부 링크 정책을 적용한다.
- HTTPS를 강제하고 비밀키는 서버 환경변수에만 저장한다.
- 날짜/국가 입력을 검증하고 사용자 입력으로 파일 경로를 만들지 않는다.
- 비루트 계정, 최소 파일 권한, nginx rate limit을 사용한다.
- 로그와 보고서에서 API 키와 인증 헤더를 마스킹한다.

### 개인정보처리방침

데이터 직접 수집 여부와 무관하게 Data Safety 양식과 정책 URL을 제공한다.

- 개발자/운영 주체와 문의 수단
- 앱/서버가 처리하는 정보와 접근 로그
- 외부 서비스와 SDK
- 처리 목적, 보관 기간, 삭제 정책
- 제3자 제공 여부
- 시행일과 변경 이력

### Android 재개 시 Google Play

아래 항목은 현재 웹 MVP 범위가 아니며 Android 트랙 재개 시 다시 검증한다.

- 개발자 계정, 신원 확인, 등록비 예산
- AAB와 Play App Signing
- 출시 시 Target API 요구사항 재확인
- 신규 개인 계정의 비공개 테스트 요건 충족
- Data Safety, 개인정보처리방침, 콘텐츠 등급
- 뉴스·잡지 앱 선언 대상임을 전제로 준비
- 앱 내 운영자 연락처, 기사 출처, 발행일 제공
- 앱 아이콘, 피처 그래픽, 스크린샷, 설명 준비
- 자동 분석 결과이며 투자 자문이 아님을 고지

```text
앱 이름: 이슈 클라우드
부제: 미국·일본·한국의 오늘 경제 이슈
짧은 설명: 세 나라가 오늘 주목한 경제 이슈를 국가별로 확인하세요.
```

---

## 13. 테스트 전략

### 백엔드·배치

- URL/제목 중복 제거와 안정적인 동률 정렬
- 날짜 범위, 시간대, 원자적 저장, 만료 삭제
- 3개국 정상 전체 흐름
- 한 국가 실패 후 나머지 계속 처리
- 2개국 부분 성공 게시, 1개국 성공 시 latest 미갱신
- LLM 형식 오류, 재시도, 근거 검증
- 장애 보고서, 비밀정보 마스킹, 중복 lock
- 외부 API/LLM은 mock과 fixture 사용

### API

- latest/dates/날짜/국가 정상 응답
- 범위 밖 400, 데이터 없음 404, 점검 503
- ETag 304와 손상 파일 처리
- 입력 경로 조작 방지

### Android(보류 트랙)

- 국가 전환 시 추가 요청 없음
- 날짜 전환 시 요청 발생
- 최초 실행 시 타일형이 표시되고 마지막 보기 선택이 재실행 후 복원됨
- 타일/클라우드 전환 시 네트워크 요청과 데이터 재집계가 발생하지 않음
- 두 보기에서 같은 이슈를 선택하면 동일한 상세 화면으로 이동함
- TOP 5 하단 중복 목록이 렌더링되지 않음
- 오늘 미준비 폴백 메시지 유지
- 오래된 비동기 응답이 최신 UI를 덮지 않음
- 오프라인 캐시와 손상 응답 방어
- 화면/프로세스 재생성 후 상태 복원
- TalkBack, 글자 확대, 긴 다국어 라벨
- 작은 화면, 태블릿, 폴더블
- release AAB의 운영 API 연결
- Android 재개 시 타일형·클라우드형·상태별 Compose 스크린샷 회귀 테스트

### LLM 회귀 평가

- `sample-data/evaluation/{US,JP,KR}`에 국가별 고정 입력을 둔다.
- `sample-data/evaluation/expected`에는 문장 전체가 아니라 Schema, 근거 ID, 중복 금지, 결정적 순위의 기대값을 둔다.
- 기본 CI는 mock만 사용하며 실제 모델 평가는 명시적인 live/evaluation 실행으로 분리한다.
- 프롬프트 또는 클러스터링 변경 시 국가 간 혼합, 입력에 없는 근거, TOP 5 중복과 비용 상한을 재검증한다.

### 웹

- 국가 로컬 전환과 날짜 API 호출
- 비활성 날짜 클릭 방지
- 로딩/부분 성공/오류 상태
- 모바일 날짜 가로 스크롤

### 주차 완료 감지 자동 리뷰

- 실행: 활성 주차의 구현·테스트·문서·`scripts/verify-all.ps1` 통과를 감지한 즉시 1회
- 중복 방지: 같은 주차 후보 SHA는 한 번만 리뷰하고 Critical/High 수정으로 SHA가 변경된 경우에만 재검증한다.
- 범위: 마지막 리뷰 이후의 커밋과 diff, 관련 테스트·빌드·정적 검사
- 평가: 보안, 정확성, 성능, 유지보수성, 테스트 충분성, 문서·아키텍처 준수
- 결과: 로컬 전용 `reviews/YYYY-MM-DD-weekly-review.md`
- 상세 기준과 템플릿: `docs/review/WEEKLY_REVIEW_GUIDE.md`, `docs/review/WEEKLY_REVIEW_TEMPLATE.md`

| 항목 | 확정 기준 |
|---|---|
| 리뷰 시간 | 최대 60분 |
| Critical/High 수정 시간 | 리뷰 후 별도 최대 90분 |
| 명령 timeout | 기본·웹 전체 20분, Android 재개 시 전체 30분 |
| 일시적 실패 재시도 | 원인 확인 후 1회 |
| 동일 finding 수정 시도 | 최대 2회, 이후 `BLOCKED` |
| 변경 코드 coverage | Line 80%, Branch 70% |
| 전체 coverage | Backend 80/70, Web 75/65, Android 재개 시 70/60 (Line/Branch) |
| 핵심 경로 | Backend 집계·Repository 90% Line, Web 상태·API·캐시 80% Line, Android 재개 시 ViewModel·Repository 80% Line |

리뷰 범위는 로컬 `reviews/.last-reviewed-sha`부터 현재 `HEAD`까지이며 리뷰가 정상 완료된 경우에만 기준 SHA를 갱신한다. 첫 리뷰는 저장소 전체 보안·설정과 최근 7일 diff를 확인한다. diff 밖의 기존 문제는 `LEGACY`로 구분하되 Critical/High는 수정한다.

필수 검사는 명세 동기화, diff 형식, secret·보안, 의존성 취약점, `scripts/verify-all.ps1`, coverage, 정확성·성능·유지보수성·아키텍처 순으로 수행한다. LLM 또는 UI 변경 시 해당 회귀 검사를 추가한다. 성능은 동일 로컬 환경 3회 중앙값으로 캐시 API p95 500ms, fixture 비캐시 API p95 1초, mock 3개국 pipeline 60초를 기준으로 한다.

LLM 변경 시 Schema 100%, 입력 밖 기사 ID·근거 0건, 국가 혼합 0건, TOP 5 중복 0건, 순위 결정성 100%, 추출 성공률 80% 이상을 요구한다. label은 국가별 최대 5개 표본에서 80% 이상 수용 가능해야 한다.

심각도 처리 정책:

| 심각도 | 처리 |
|---|---|
| Critical | 즉시 안전하게 수정하고 재검증한다. 리뷰에 `RESOLVED`와 수정 근거를 남긴다. 수정 불가능하면 `UNRESOLVED/BLOCKED`로 기록한다. |
| High | Critical과 동일하게 수정·재검증하고 해결 상태를 기록한다. |
| Medium | 코드를 자동 수정하지 않고 파일·라인·영향·권장 조치를 리뷰 이력에 남긴다. |
| Low | 코드를 자동 수정하지 않고 개선 후보로 리뷰 이력에 남긴다. |

리뷰 최종 상태는 `PASS`, `PASS_WITH_FINDINGS`, `FAIL`, `BLOCKED` 중 하나다. finding ID는 `WR-YYYYMMDD-NNN` 형식이며 같은 파일·규칙·원인은 fingerprint로 중복 생성을 막는다. Medium 3회, Low 4회 연속 미해결은 우선 검토 대상으로 표시하지만 기간만으로 심각도를 자동 승격하지 않는다.

`reviews/`는 `.gitignore`에 포함하고 모든 리뷰 MD를 로컬에만 저장한다. Critical/High 수정은 `codex/review-fix-YYYY-MM-DD` 브랜치에서 관련 검증을 통과시킨 뒤 명확한 수정 커밋과 Draft PR로 `main`에 반영한다. 해결된 항목은 로컬 리뷰에 `RESOLVED`, 수정 커밋 SHA와 PR 번호를 표시한다. Critical/High가 없으면 브랜치·커밋·PR 없이 로컬 리뷰만 남긴다. 외부 계약, 자격증명, 사용자 결정이 필요한 항목은 임의로 우회하지 않는다.

---

## 14. 배포와 운영

```text
1차 운영
GitHub Actions schedule/workflow_dispatch
  → 수집·LLM·집계·Schema 검증
  → 정적 웹 + data/v1 JSON artifact
  → GitHub Pages HTTPS

후속 운영
Internet → nginx/ALB → FastAPI/uvicorn
VPS/EC2 systemd 또는 container scheduler → 동일 batch entry
```

```text
deploy/
├── setup_server.sh
├── deploy.sh
├── rollback.sh
├── nginx/
├── systemd/
└── README.md
```

- 1차 Pages 배포는 공식 Pages artifact 방식으로 수행하며 생성 JSON을 `main`에 자동 커밋하지 않는다.
- PR은 mock·fixture로만 검증하고, 실제 뉴스·LLM Secret은 보호된 예약/수동 운영 workflow에서만 사용한다.
- 생성과 Schema 검증이 실패하면 기존 Pages 배포를 유지하고 실패한 artifact를 게시하지 않는다.
- Pages artifact에는 최근 7일의 공개 가능 JSON, 정적 웹, 정책 페이지만 포함한다.
- VPS/EC2 후속 배포는 최초 설정과 반복 배포를 분리하고 `/health`, `/ready`, 롤백과 최근 2개 릴리스 보관을 적용한다.

운영 지표:

- 배치 시간, 국가·소스별 기사 수와 실패율
- LLM 호출, 토큰, 비용, 재시도, 성공률
- 마지막 게시 성공 시각
- Actions 실행·Pages 배포 성공 여부와 마지막 게시 성공 시각
- 후속 API 모드의 요청 수, 오류율, 응답시간
- 24시간 지연 시 안내, 48시간 지연 시 웹 경고

운영 런북에는 Actions 예약 지연·비활성화, 수동 재실행, Pages artifact 롤백, 소스 인증/형식 변경, LLM 비용 급증과 JSON 복구를 포함한다. VPS/EC2 재개 시 서비스 재시작, 인증서 실패, 서버 롤백 절차를 추가한다.

---

## 15. GitHub와 CI/CD

Git 제외 항목:

```text
.env
.env.* (`.env.example` 제외)
secrets/
credentials/
*.jks
*.keystore
*.p12
*.pfx
*.pem
key.properties
keystore.properties
google-services.json
*service-account*.json
firebase-adminsdk*.json
local.properties
data/
reports/
reviews/
logs/
*.log
*.db
*.sqlite*
.vscode/settings.json
.vscode/launch.json
```

### 파일별 Secret 관리

| 파일·영역 | 예상 민감정보 | 개발 환경 저장 위치 | 운영 환경 저장 위치 | Git 정책 |
|---|---|---|---|---|
| `backend/.env` | 뉴스 API 키, NAVER Client ID/Secret, LLM 키, DB URL, JWT/Admin Secret | 로컬 비추적 파일 | 1차 GitHub Environment Secrets, 후속 `/etc/country-issue-cloud/backend.env` 또는 cloud Secret | 커밋 금지 |
| `backend/.env.example` | 환경변수 이름과 비민감 예시 | 저장소 | 저장소 | 실제 값 없이 커밋 허용 |
| `backend/app/config.py` | 환경변수 Schema와 검증 규칙 | 저장소 | 배포 코드 | 값 하드코딩 금지, 변수명만 허용 |
| `android/local.properties` | SDK 경로와 로컬 설정 | 개발자 PC | 해당 없음 | 커밋 금지 |
| `key.properties`, `keystore.properties`, `*.jks`, `*.keystore` | 앱 서명키와 비밀번호 | Git 외부 암호화 보관 | Play App Signing/CI Secret | 커밋 금지 |
| Android `BuildConfig`, `strings.xml`, Kotlin 소스 | 백엔드 URL, 실수로 입력한 provider key | 공개 가능한 URL만 포함 | AAB/APK에 포함 | 외부 API/LLM key와 Client Secret 금지 |
| `google-services.json`, 서비스 계정 JSON | Firebase client 설정 또는 관리자 credential | 필요 시 별도 전달 | 호스팅 Secret | 기본 커밋 금지, 서비스 계정은 절대 금지 |
| `.github/workflows/*.yml` | 뉴스·LLM·Pages·후속 배포 credential | `${{ secrets.NAME }}` 참조 | GitHub Environment Secrets | 평문 값·PR Secret 노출 금지 |
| Pages 배포 artifact `data/v1/` | 공개 이슈 결과와 기사 metadata | CI 임시 workspace | GitHub Pages | 공개 가능 필드만 포함, Secret·원문·raw log 금지 |
| `deploy/`, Docker, systemd 설정 | DB 비밀번호, API key, SSH key | 변수 참조만 저장 | 서버 환경변수·Secret 저장소 | 평문 값 금지 |
| `tests/fixtures/`, `sample-data/` | 실제 응답의 token, header, 작성자 개인정보 | 비식별 mock/fixture | 해당 없음 | 가공 데이터만 허용 |
| `logs/`, `data/`, `*.db`, 일일보고서·리뷰 | 인증 header, IP, 기기정보, 원문 응답 | 로컬 전용·마스킹 | 접근 제한 저장소 | raw 민감정보 커밋 금지 |
| `.vscode/launch.json`, IDE 실행 설정 | 실행 환경변수와 token | 개발자 PC | 해당 없음 | 민감값 포함 파일 커밋 금지 |

Android 바이너리는 역분석 가능하다고 가정한다. `API_BASE_URL`과 공개용 OAuth Client ID만 앱에 포함할 수 있으며 뉴스 API 키, LLM 키, NAVER Client Secret, DB credential, 관리자 token, JWT 서명키와 서명 비밀번호는 백엔드 또는 배포 Secret에만 둔다. Client ID도 제공자 정책상 비밀로 분류되면 서버 전용으로 처리한다.

### 커밋 차단 기준

- `scripts/check-secrets.ps1`은 Git 추적 파일명과 고신뢰 secret 패턴을 검사하며 `scripts/verify-all.ps1`의 필수 단계로 실행한다.
- `.env.example`에는 변수명, 빈 값, 명백한 placeholder만 허용한다. 실제와 유사한 예시 키를 사용하지 않는다.
- 비밀 파일, private key, provider token 또는 credential이 발견되면 검증과 커밋을 실패 처리한다.
- 로그, fixture, 문서, 스크린샷에는 `Authorization`, cookie, 개인식별정보, 전체 외부 응답을 넣지 않는다.
- PR CI에서도 동일 검사와 GitHub secret scanning/push protection을 사용한다. 로컬 검사는 서버 측 보호를 대체하지 않는다.
- 의심 값은 허용 목록으로 우회하지 않고 저장 위치를 Secret 저장소로 변경한다. 예외가 필요하면 사용자 승인과 ADR을 요구한다.
- 유출된 key는 Git에서 문자열을 삭제하는 것만으로 해결된 것으로 보지 않는다. 즉시 폐기·재발급하고 영향 범위 확인 후 필요하면 저장소 이력을 정리한다.

README에는 앱/웹 링크, 스크린샷, 아키텍처, 기술 선택, 실행법, API 예시, 테스트, 출처·LLM·운영 정책을 포함한다. MIT License, secret scanning, 의존성 업데이트, Issue/PR 템플릿을 사용한다.

Pull Request CI:

- 공통: 한·일 명세 동시 변경과 핵심 구조 동기화 검사
- Python: Ruff, mypy, pytest, import 경계, 보안 검사
- Android(보류): 트랙 재개 시에만 ktlint, detekt, Android Lint, 테스트, debug 빌드
- 웹: 정적 검사, JS 테스트, DataSource 계약, 기본 접근성 검사
- Pages: fixture 기반 build, 공개 artifact Secret 검사, 링크·JSON Schema smoke test

```text
main merge → 병합된 main 전체 CI·로컬 smoke 재검증 → fixture Pages preview/build 검증
보호된 schedule/workflow_dispatch → 실제 배치 → Schema·Secret 검사 → Pages artifact 배포 → 실패 시 기존 배포 유지
VPS/EC2 재개 후 → ApiDataSource 설정 → server 배포 → health/ready → 실패 시 롤백
v* 태그 → Pages URL 검증 → GitHub Release. Android 재개 후에만 AAB와 Play 내부 테스트 트랙을 추가한다.
```

### AI 개발 가드레일

- 구현 작업은 목표, 범위, 제외 범위, 완료 조건, 검증 명령, 주차 커밋을 포함하는 작업 계약을 따른다.
- `docs/AI_DEVELOPMENT_GUIDE.md`와 일본어판을 AI 작업의 실행 기준으로 사용한다.
- `docs/DEVELOPMENT_STATUS.md`와 일본어판에 현재 목표, 완료 커밋, 검증 결과, 다음 작업과 외부 의존성을 기록한다.
- 개발 작업이 수행된 날에는 종료 시점에 `docs/daily/YYYY-MM-DD.md`를 작성한다. 한 파일에 한국어·일본어 내용을 함께 기록하고 목표 최종 커밋과 PR에 포함한다.
- 공통 완료 조건에는 기능·오류 경로, 관련 테스트, lint/type/build, 비밀정보 검사, 문서 동기화와 일본어 주석 규칙을 포함한다.
- 주차 커밋 전에 `scripts/verify-all.ps1`을 실행한다. 이 스크립트는 명세 동기화와 생성된 각 프로젝트의 검사를 한 진입점에서 수행한다.
- 주차 브랜치의 임시 WIP 커밋은 허용하되 주차 완료 감지 리뷰 후 squash 또는 amend하여 주차 단위 커밋 하나로 정리한다.
- 각 개발 주차는 지정된 `codex/week-*` 브랜치에서 진행하고 `main` 대상 Draft PR 하나로 게시한다.
- 통합 검증과 CI, 리뷰 통과 후 Ready로 전환하고 **Rebase and merge**로 병합해 검증된 주차 커밋 제목과 선형 이력을 유지한다.
- `Create a merge commit`은 사용하지 않는다. 로컬 WIP squash가 불가능했던 예외에만 `Squash and merge`를 허용하며 squash 커밋 제목을 날짜·3개 언어 형식으로 직접 지정한다.
- 목표 변경을 `main`에 직접 push하지 않는다.
- 병합 후 최신 `main`에서 `scripts/verify-all.ps1`과 가능한 로컬 smoke test를 다시 실행해 병합 충돌, 의존성 조합과 통합 오류를 확인한다.
- 병합 후 검증이 통과해야 해당 주차가 완료된다. 실패하면 `codex/post-merge-fix-week-<number>` 브랜치와 별도 PR로 수정하며 `main`을 직접 고치지 않는다.
- 병합 후 검증 통과 뒤 주차 브랜치를 삭제하고, 검증된 최신 `main`에서 다음 주차 브랜치를 만든다.
- AI가 API 계약, 핵심 아키텍처, 기술 스택, 비용·공개 범위를 바꾸려면 ADR과 사용자 확인이 필요하다.
- UI 스크린샷 기준 변경은 자동 승인하지 않고 사람이 의도된 변경인지 확인한다.

---

## 16. 비용 계획

| 항목 | 정책 |
|---|---|
| Google Play | 일회성 등록비 반영 |
| GitHub Pages | 공개 포트폴리오 용도와 무료 제공량 내 운영 |
| VPS/EC2·도메인 | 후속 전환 시에만 저가 월 고정비와 예산을 사전 확정 |
| NewsAPI | 운영 사용 안 함, 로컬 개발만 |
| 운영 뉴스 소스 | 무료·허용 소스 우선 |
| LLM | 월 USD 10 상한 |
| HTTPS | 1차 Pages 기본 HTTPS, 후속 무료 인증서 또는 cloud 인증서 |
| GitHub Actions | 공개 저장소 표준 runner와 무료 제공량 내 목표, larger runner 금지 |

외부 서비스 요금과 약관은 프로덕션 배포 직전에 다시 확인한다.

---

## 17. 개발 일정

2026년 8월 3일 월요일부터 시작하는 AI 개발 지원 기반의 로컬 우선 일정이다. fixture, 로컬 FastAPI와 브라우저로 개발한 뒤 3주 안에 GitHub Actions + GitHub Pages 반응형 웹 MVP를 공개한다. FastAPI와 ApiDataSource는 후속 VPS/EC2 호환 경계로 유지하되 서버 계약·배포는 현재 완료 조건에서 제외한다. 날짜별 표는 기준선으로 유지하되 작업을 앞당길 수 있다. 리뷰는 고정 요일이 아니라 각 주차의 구현·테스트·문서·전체 검증 완료를 감지한 즉시 실행한다. 토·일요일은 지연 보완과 사용자 확인을 위한 버퍼다. Android·Play 연동은 별도 재개 결정 이후에만 일정을 세운다.

### 일일 개발 보고서 정책

- 경로: `docs/daily/YYYY-MM-DD.md` (`Asia/Tokyo` 기준)
- 형식: `docs/daily/TEMPLATE.md`를 사용하고 한 파일 안에 동등한 한국어·일본어 섹션을 작성한다.
- 내용: 오늘의 목표, 수행 작업, 주요 변경 파일, 검증 결과, 결정사항, 문제·리스크, 다음 작업
- 실패·미완료 작업도 원인과 후속 조치와 함께 기록한다.
- 비밀키, 토큰, 인증 헤더, 개인정보와 원문 로그 전체는 포함하지 않는다.
- Git 추적 대상으로 주차 브랜치에 저장하며, 별도 일일 커밋 없이 해당 주차의 최종 커밋과 PR에 포함한다.
- 주차 완료 감지 리뷰의 `reviews/*.md`는 계속 로컬 전용으로 유지하고 일일 보고서와 혼합하지 않는다.

### 주차별 개발 목표 요약

| 주차 | 기간 | 포함 목표 | 주간 완료 기준 |
|---|---|---|---|
| 1주차 | 8/3~8/8 | 목표 1 환경·골격, 목표 2 데이터·API, 목표 3 수집·정제 | 로컬 API와 3개국 수집 기반 동작 |
| 2주차 | 8/10~8/15 | 목표 4 LLM·TOP 5, 목표 5 배치·웹 기반 | 국가별 TOP 5를 배치→정적 JSON/FastAPI→웹으로 시연 |
| 3주차 | 8/17~8/22 | 목표 6 웹 UI, 목표 7 캐시·접근성, 목표 8 Pages 공개 | 실제 URL과 자동 갱신을 검증하고 `v0.8.0-pages-mvp` 공개 |

### 1주차 — 기반, 로컬 API, 국가별 수집

| 날짜 | 개발 내용 | 당일 산출물·검증 |
|---|---|---|
| 8/3(월) | 환경 점검, monorepo, 설정 분리, fixture, 기본 CI, AI 개발 검증 진입점 | 목표 1 검증 후 목표 커밋 템플릿 적용 |
| 8/4(화) | 데이터 모델, Schema, JSON Repository 구현 | 정상·오류 fixture와 Repository 테스트 |
| 8/5(수) | 원자적 저장, 보관 정책, FastAPI 전체 엔드포인트 | 목표 2 중간 검증, 커밋 없이 주차 브랜치 유지 |
| 8/6(목) | Collector 계약, fixture·실제 소스 어댑터, 중복 제거 | 동일 출력 Schema와 중복 제거 테스트 |
| 8/7(금) | 국가별 병렬 수집, 실패 격리, `fixture/live/mixed` 모드 | 1주차 전체 검증 후 후보 커밋·Draft PR |
| 8/8(토) | 1주차 지연 보완·사용자 확인 버퍼 | 미완료 항목이 있을 때만 보완 |

### 2주차 — LLM, 전체 배치, 웹 기반

| 날짜 | 개발 내용 | 당일 산출물·검증 |
|---|---|---|
| 8/10(월) | LLM 인터페이스, mock, 구조화 출력, 실제 어댑터 | 외부 호출 없는 테스트와 제한된 실호출 검증 |
| 8/11(화) | 국가 내부 클러스터링, 근거 검증, 결정적 TOP 5 | 유사 표현 병합·환각 방지·동률 테스트 |
| 8/12(수) | 캐시, timeout·retry, 토큰·비용 기록과 품질 리뷰 | 목표 4 중간 검증, 커밋 없이 주차 브랜치 유지 |
| 8/13(목) | 전체 pipeline, 부분 성공, lock, retry, 보고서 | 한 국가 실패·중복 실행·마스킹 테스트 |
| 8/14(금) | 정적 JSON publisher, DataSource 기반 웹과 통합 실행 | 2주차 전체 검증 후 후보 커밋·Draft PR |
| 8/15(토) | 2주차 지연 보완·사용자 확인 버퍼 | 미완료 항목이 있을 때만 보완 |

### 3주차 — 반응형 웹 UI, 캐시, Pages 공개

| 날짜 | 개발 내용 | 당일 산출물·검증 |
|---|---|---|
| 8/17(월) | IssueDataSource 두 adapter, 반응형 기본 화면 | static/API 계약과 기본 화면 테스트 |
| 8/18(화) | 국가·날짜 선택, C안 타일, A안 클라우드, 상세 | 표시·전환·상세 흐름 테스트 |
| 8/19(수) | localStorage, Cache API/IndexedDB, 오류·접근성 | 캐시 복구·키보드·확대 검증 |
| 8/20(목) | Actions schedule/manual workflow, concurrency, Pages 배포 | fixture artifact와 실패 시 기존 배포 유지 검증 |
| 8/21(금) | 전체 회귀, Secret 검사, README·스크린샷·Release 후보 | 주차 후보 커밋과 Draft PR 생성 |
| 8/22(토) | 최종 지연 보완·출시 확인 버퍼 | 미완료 항목이 있을 때만 보완 |

### 주차 단위 커밋·PR 정책

목표 1 스캐폴드는 이미 별도 PR로 완료했으며, 남은 개발은 다음 세 주차 단위로 관리한다.

| 주차 | 작업 브랜치 | 포함 목표 | 최종 커밋 메시지 |
|---|---|---|---|
| 1주차 | `codex/week-01-data-collection` | 목표 2 데이터·API, 목표 3 국가별 수집 | `YYYY/MM/DD feat: implement local data and collection`<br>`로컬 데이터와 국가별 수집 구현`<br>`ローカルデータと国別収集を実装` |
| 2주차 | `codex/week-02-pipeline-publishing` | 목표 4 LLM·TOP 5, 목표 5 배치·정적 게시 | `YYYY/MM/DD feat: complete issue pipeline and static publishing`<br>`이슈 파이프라인과 정적 게시 완성`<br>`イシューパイプラインと静的公開を完成` |
| 3주차 | `codex/week-03-pages-mvp` | 목표 6 웹 UI, 목표 7 캐시·접근성, 목표 8 Pages 공개 | `YYYY/MM/DD release: publish GitHub Pages MVP`<br>`GitHub Pages MVP 공개`<br>`GitHub Pages MVPを公開` |

각 주차는 브랜치 하나, 최종 커밋 하나, Draft PR 하나를 사용한다. 주차 범위가 완료되는 즉시 후보 커밋을 만들고 자동 리뷰를 실행한다. Critical/High 수정은 같은 커밋을 amend한 뒤 `--force-with-lease`로 갱신한다. Medium/Low는 로컬 리뷰 이력만 남긴다. CI·리뷰 통과 후 **Rebase and merge**하며, 병합 직후 최신 `main`에서 전체 검증과 smoke test가 통과해야 주차를 완료 처리한다.

### 후속 선택 일정 — VPS/EC2 전환

| 영업일 | 개발·운영 내용 | 완료 기준 |
|---|---|---|
| 1일차 | VPS 또는 EC2, 도메인, 비루트 계정/IAM과 방화벽 준비 | 기본 서버·cloud 보안 점검 통과 |
| 2일차 | nginx, TLS, FastAPI systemd 서비스 배포 | HTTPS API 접근 가능 |
| 3일차 | 배치 service/timer와 운영 환경변수 적용 | 수동·예약 배치 성공 |
| 4일차 | server 배포 workflow, health/ready, 롤백 구성 | 배포·검증·롤백 리허설 |
| 5일차 | `DATA_MODE=api` 전환, CORS/CSP, 주요 화면 smoke test | UI 로직 변경 없이 운영 API 연결 |
| 이후 7일 | 자동 배치와 비용·오류·데이터 품질 관찰 | 7일 연속 운영 기록 |

### Android 재개 결정 후 별도 일정 — Play 테스트와 출시

| 단계 | 개발·출시 내용 | 완료 기준 |
|---|---|---|
| 1~2일차 | 개인정보처리방침, Data Safety, 뉴스 앱 선언 정리 | Play 제출 문서 완성 |
| 3일차 | 서명된 release AAB와 스토어 이미지·설명 준비 | 내부 테스트 업로드 |
| 4~5일차 | 내부 테스트, 실제 기기 smoke test, 결함 수정 | 핵심 사용자 흐름 통과 |
| 정책 요구 기간 | 비공개 테스트 운영과 피드백 반영 | 요구 테스터 수·기간 충족 |
| 출시일 | `v1.0.0`, GitHub Release, Play 단계적 출시 | Play 링크·Live Demo·공개 GitHub 제공 |

| 출시 후 주기 | 작업 |
|---|---|
| 매일 | 배치와 최신 데이터 자동 확인 |
| 매주 | 장애, 비용, 매체 편중 검토 |
| 매월 | 의존성, 복구 테스트, 비용 검토 |
| 90일 | 뉴스 소스 약관 재확인 |
| 정책 변경 시 | Target SDK, Data Safety, SDK 정책 검토 |

---

## 18. 버전 계획

```text
v0.1.0 설계와 스캐폴드
v0.2.0 Repository와 FastAPI
v0.3.0 뉴스 수집과 정제
v0.4.0 LLM 이슈 추출과 집계
v0.5.0 배치 리뷰와 장애 보고서
v0.6.0 웹 기반과 전체 파이프라인
v0.7.0 반응형 웹 핵심 UI
v0.8.0 오프라인과 안정화
v0.9.0 공개 웹 배포와 운영 검증
v1.0.0 첫 공개 릴리스
```

---

## 19. 출시 게이트

- [x] 수집이 특정 주제 검색에 편향되지 않음
- [x] 최소 2개국 운영 소스 이용조건 확인
- [ ] 7일 연속 자동 배치 결과 확보
- [x] 한 국가 실패 시 다른 국가 결과 유지
- [x] LLM 결과에 없는 기사/표현이 포함되지 않음
- [x] API 200/400/404/503 검증
- [x] 웹 브라우저 캐시와 복구 검증
- [ ] 공개 웹 URL에서 주요 화면과 API가 동작
- [x] 개인정보처리방침, 문의, 출처, 발행일 표시
- [x] GitHub에 비밀키와 운영 데이터가 없음
- [x] Pages 배포 실패 시 기존 정상 artifact 유지·롤백 검증
- [ ] VPS/EC2 재개 시 server 롤백 검증
- [ ] Android 재개 시 Play 선언과 테스트 요건 충족
- [x] README에서 실제 앱/웹/설계/테스트 확인 가능

---

## 20. 주요 리스크

| 리스크 | 대응 |
|---|---|
| 무료 소스 부족/약관 변경 | 다중 어댑터, 설정화, 실제 표본 공개 |
| 검색어 편향 | 카테고리/RSS 전체 수집, 쿼리 기록 |
| LLM 오분류 | ID/근거 검증, 샘플 리뷰, 버전 관리 |
| LLM 비용 증가 | 묶음 처리, 캐시, 월 USD 10 상한 |
| 국가 수집 실패 | 독립 처리, 부분 성공, 지연 안내 |
| JSON 손상 | 임시 작성, 검증, 원자적 교체 |
| Actions 예약 지연·비활성화 | 정각 비의존, 수동 실행, 마지막 정상 Pages 유지 |
| 후속 VPS/EC2 장애 | health monitor, systemd/container, 캐시, 롤백 |
| Android 재개 후 Play 심사 지연 | 재개 시 정책 자료 준비와 일정 버퍼 재산정 |
| 공개 저장소 키 유출 | `.gitignore`, secret scan, 키 회전 |

---

## 21. 최종 산출물

- [ ] 통합 명세, 화면/기능/아키텍처 설계서와 ADR
- [x] 데이터·출처 정책과 API 명세
- [x] Python 배치와 FastAPI
- [x] 반응형 웹 애플리케이션
- [x] Android 후속 트랙 보류 기록
- [x] 자동 테스트와 CI/CD
- [x] GitHub Actions 배치·Pages 배포 workflow
- [ ] 후속 VPS/EC2용 배포 스크립트, nginx, systemd/container 템플릿
- [ ] 운영 런북과 장애 보고서 예시
- [x] 개인정보처리방침과 문의 페이지
- [ ] Android 재개 시 Google Play 등록 자료
- [ ] README, 데모 이미지, GitHub Release
- [ ] 개발일별 한·일 병기 일일 보고서

---

## 22. 최종 정의

> 국가별 이슈 클라우드는 미국·일본·한국의 경제뉴스를 국가별로 독립 수집하고, LLM으로 각 국가 내부의 유사한 기사 표현을 이슈 단위로 묶은 뒤, 고유 기사 수와 매체 다양성에 따라 국가별 TOP 5를 URL로 보여주는 반응형 웹 서비스다. 결과에는 실제 출처와 표본 수를 제공하며, 배치 실패·캐시 복구·외부 API 비용과 같은 운영 문제를 명시적으로 처리한다. Android 앱은 공개 웹 안정화 후 선택적으로 재개할 수 있도록 API 계약과 설계 기록을 보존한다.
