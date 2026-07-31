# 국가별 이슈 클라우드 (Country Issue Cloud)

> 미국·일본·한국의 경제뉴스를 국가별로 독립 분석하고, 각 국가가 그날 주목한 경제 이슈를 의미 기반 클라우드로 보여주는 Android 애플리케이션

## 문서 정보

| 항목 | 내용 |
|---|---|
| 목적 | 기획·설계·개발·테스트·배포·운영의 단일 기준 |
| 프로젝트명 | 국가별 이슈 클라우드 |
| 영문명 | Country Issue Cloud |
| 앱 이름 | 이슈 클라우드 |
| 저장소명 | `country-issue-cloud` |
| 기준 시간대 | `Asia/Tokyo` |

중요한 설계 변경은 이 문서와 코드에 함께 반영하고 `docs/adr/`에 ADR로 남긴다.

---

## 1. 프로젝트 개요

매일 미국·일본·한국의 경제뉴스를 국가별로 독립 수집한다. 각 국가 안에서 의미가 유사한 기사와 표현을 하나의 이슈로 묶고, 고유 기사 수와 매체 다양성을 기준으로 국가별 TOP 5를 계산한다. 사용자는 같은 날짜에 각 나라가 무엇을 중요하게 다뤘는지 국가 탭을 전환하며 확인한다.

이 프로젝트는 다음 목적을 가진 비상업적 포트폴리오다.

1. 실제 Android 앱을 제작해 Google Play에 배포한다.
2. GitHub에 설계, 개발, 테스트, 배포 이력을 공개한다.
3. 매일 데이터가 갱신되는 서비스를 실제 운영한다.
4. 다국어 처리, LLM 구조화 출력, 배치/API 분리, 오프라인, CI/CD 역량을 증명한다.

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

- Android 앱이 Google Play 프로덕션 또는 공개 가능한 테스트 트랙에 등록된다.
- 최소 2개국 결과가 매일 자동 갱신된다.
- 최근 7일의 국가별 TOP 5와 근거 기사를 확인할 수 있다.
- 오프라인에서 마지막 정상 데이터를 볼 수 있다.
- 웹 데모와 운영 API가 외부에서 접근 가능하다.

| 지표 | 목표 |
|---|---:|
| 최근 30일 배치 게시 성공률 | 95% 이상 |
| API 가용성 내부 목표 | 99% 이상 |
| 캐시 적중 API 응답시간 | 500ms 이내 |
| 마지막 정상 데이터 | 48시간 이내 |
| 국가별 정상 권장 표본 | 30개 이상 |
| 국가별 게시 가능 표본 | 15개 이상 |
| 이슈 추출 성공률 | 80% 이상 |

### 1차 출시 포함

- 국가별 수집, 정제, 중복 제거, 이슈 클러스터링, TOP 5
- 최근 7일 JSON 저장과 FastAPI
- Android 클라우드, 목록, 상세, Room 캐시
- 부분 성공, 지연, 점검, 오류 상태
- 정적 웹 데모
- 자동 리뷰와 Markdown 장애 보고서
- VPS, HTTPS, systemd, GitHub Actions
- Google Play 테스트와 출시 준비

### 1차 제외

- 로그인, 댓글, 광고, 결제, 개인화 추천
- 서버 동기화 즐겨찾기, 푸시 알림
- iOS, 7일 초과 이력, 실시간 스트리밍

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
| F-10 | 정기 실행 | systemd timer와 제한 재시도 |
| F-11 | 날짜 조회 | 최근 7일 조회 가능 날짜 제공 |
| F-12 | 국가 전환 | 같은 날짜의 국가별 결과 즉시 전환 |
| F-13 | 클라우드 | 기사 비중 기반 태그 클라우드 |
| F-14 | 상세 | 통계, 대표 기사, 원문 링크 |
| F-15 | 오프라인 | Room 캐시로 최근 결과 표시 |
| F-16 | 앱 설정 | 점검, 버전, 공지, 정책 URL |
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
- 일본 공식 소스와 NAVER API HUB의 운영 조건 확인은 출시 게이트다.
- 소스별 이용조건 확인일과 허용 필드를 설정에 기록한다.

```yaml
sources:
  US:
    - id: federal_reserve
      type: rss
      enabled: true
      terms_checked_at: "YYYY-MM-DD"
      allowed_fields: [title, summary, url, publisher, published_at]
  JP: []
  KR: []
```

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

기본 경로는 `/api/v1`이다.

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
- nginx rate limit을 적용한다.

---

## 9. Android 앱 설계

| 구분 | 선택 |
|---|---|
| 언어/UI | Kotlin, Jetpack Compose, Material 3 |
| 구조 | UI → ViewModel → Repository → Room/API |
| 네트워크 | Retrofit 또는 Ktor 중 구현 시 하나로 확정 |
| JSON | Kotlinx Serialization |
| 저장 | Room, DataStore |
| 비동기/DI | Coroutines, Flow, Hilt |
| 최소 SDK | API 26 |
| Target SDK | 출시 시 Play 요구사항 충족, 초기 목표 API 36 |
| 배포 | AAB, Play App Signing |

### 화면

1. 초기 로딩
2. 이슈 클라우드 홈
3. 이슈 상세와 대표 기사
4. 프로젝트 정보
5. 개인정보처리방침/문의
6. 오픈소스 라이선스
7. 점검/업데이트 안내

홈 화면은 앱 제목/기준일, 국가 탭, 최근 7일, 분석 기사 수, 클라우드, TOP 5, 새로고침 순이다. 국가 탭은 같은 날짜 응답을 사용해 추가 요청 없이 전환하고 날짜 변경 때만 요청한다.

### 클라우드 규칙

- 국가별 `article_ratio`로 글자 크기를 계산한다.
- 최소/최대 크기를 제한하고 순위 기반 결정적 배치를 사용한다.
- 무작위 회전, 과도한 색상, 색상만으로 구분하는 방식을 피한다.
- 포인트 컬러 하나와 명도 차이만 사용한다.
- 긴 라벨은 최대 두 줄, 선택하면 상세 화면으로 이동한다.

### 상태

| 상태 | 처리 |
|---|---|
| 정상 | 클라우드와 TOP 5 표시 |
| 로딩 | 스켈레톤과 입력 제한 |
| 오늘 미준비 | 최신 날짜 폴백과 안내 |
| 부분 성공 | 해당 국가에 제한 안내 |
| 국가 실패 | 해당 국가만 갱신 지연 표시 |
| 오프라인+캐시 | 캐시와 마지막 확인 시각 |
| 오프라인+캐시 없음 | 연결 안내와 재시도 |
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
├── config/
├── deploy/
├── docs/
│   ├── architecture.md
│   ├── functional-design.md
│   ├── screen-design.md
│   ├── api-spec.md
│   ├── data-policy.md
│   ├── deployment-guide.md
│   ├── operations-runbook.md
│   └── adr/
├── sample-data/
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

JSON을 SQLite/PostgreSQL로 바꿔도 Router, Service, Android API 계약은 유지한다.

웹 데모는 정적 HTML/CSS/Vanilla JS로 만들고 Android와 같은 API와 상태 정의를 사용한다. 최대 폭 720px, 포인트 컬러 하나, 단순한 클라우드 디자인을 적용한다.

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

systemd timer에 `Persistent=true`를 사용한다. 이미 게시된 날짜는 기본적으로 건너뛰며 OS 파일 잠금으로 동시 실행을 막는다.

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

## 12. 보안·개인정보·Google Play

### 앱과 서버

- 로그인, 광고, 위치·연락처·사진·저장소 권한을 사용하지 않는다.
- Android는 `INTERNET` 권한만 사용한다.
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

### Google Play

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

### Android

- 국가 전환 시 추가 요청 없음
- 날짜 전환 시 요청 발생
- 오늘 미준비 폴백 메시지 유지
- 오래된 비동기 응답이 최신 UI를 덮지 않음
- 오프라인 캐시와 손상 응답 방어
- 화면/프로세스 재생성 후 상태 복원
- TalkBack, 글자 확대, 긴 다국어 라벨
- 작은 화면, 태블릿, 폴더블
- release AAB의 운영 API 연결

### 웹

- 국가 로컬 전환과 날짜 API 호출
- 비활성 날짜 클릭 방지
- 로딩/부분 성공/오류 상태
- 모바일 날짜 가로 스크롤

### 주간 자동 리뷰

- 실행: 2026년 8월 8일부터 9월 26일까지 매주 토요일 10:00(JST)
- 범위: 마지막 리뷰 이후의 커밋과 diff, 관련 테스트·빌드·정적 검사
- 평가: 보안, 정확성, 성능, 유지보수성, 테스트 충분성, 문서·아키텍처 준수
- 결과: `reviews/YYYY-MM-DD-weekly-review.md`

심각도 처리 정책:

| 심각도 | 처리 |
|---|---|
| Critical | 즉시 안전하게 수정하고 재검증한다. 리뷰에 `RESOLVED`와 수정 근거를 남긴다. 수정 불가능하면 `UNRESOLVED/BLOCKED`로 기록한다. |
| High | Critical과 동일하게 수정·재검증하고 해결 상태를 기록한다. |
| Medium | 코드를 자동 수정하지 않고 파일·라인·영향·권장 조치를 리뷰 이력에 남긴다. |
| Low | 코드를 자동 수정하지 않고 개선 후보로 리뷰 이력에 남긴다. |

Critical/High 수정과 리뷰 문서는 관련 검증이 통과할 때만 하나의 명확한 커밋으로 만들고 `origin/main`에 push한다. Critical/High가 없으면 리뷰 문서만 커밋·push한다. 외부 계약, 자격증명, 사용자 결정이 필요한 항목은 임의로 우회하지 않는다.

---

## 14. 배포와 운영

```text
Internet
  → nginx (80/443, TLS)
      → /       정적 웹
      → /api/   FastAPI/uvicorn

systemd
  → issue-cloud-api.service
  → issue-cloud-batch.service
  → issue-cloud-batch.timer
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

- 최초 설정과 반복 배포를 분리한다.
- 배포 후 `/health`, `/ready`를 검증한다.
- 실패하면 직전 정상 릴리스로 롤백한다.
- 서버에는 최근 2개 릴리스를 보관한다.

운영 지표:

- 배치 시간, 국가·소스별 기사 수와 실패율
- LLM 호출, 토큰, 비용, 재시도, 성공률
- 마지막 게시 성공 시각
- API 요청 수, 오류율, 응답시간
- 24시간 지연 시 안내, 48시간 지연 시 앱 경고

운영 런북에는 소스 인증/형식 변경, LLM 비용 급증, JSON 복구, 서비스 재시작, 인증서 실패, 롤백 절차를 포함한다.

---

## 15. GitHub와 CI/CD

Git 제외 항목:

```text
.env
*.jks
*.keystore
key.properties
google-services.json
local.properties
data/
reports/
*.log
```

README에는 앱/웹 링크, 스크린샷, 아키텍처, 기술 선택, 실행법, API 예시, 테스트, 출처·LLM·운영 정책을 포함한다. MIT License, secret scanning, 의존성 업데이트, Issue/PR 템플릿을 사용한다.

Pull Request CI:

- Python: Ruff, mypy, pytest, import 경계, 보안 검사
- Android: ktlint, detekt, Android Lint, 테스트, debug 빌드
- 웹: 정적 검사, JS 테스트, 기본 접근성 검사

```text
main merge → 전체 CI → VPS 배포 → health/ready → 실패 시 롤백
v* 태그 → release AAB → GitHub Release → Play 내부 테스트 트랙
```

---

## 16. 비용 계획

| 항목 | 정책 |
|---|---|
| Google Play | 일회성 등록비 반영 |
| VPS/도메인 | 저가 월 고정비 사전 확정 |
| NewsAPI | 운영 사용 안 함, 로컬 개발만 |
| 운영 뉴스 소스 | 무료·허용 소스 우선 |
| LLM | 월 USD 10 상한 |
| HTTPS | 무료 인증서 |
| GitHub Actions | 무료 제공량 내 목표 |

외부 서비스 요금과 약관은 프로덕션 배포 직전에 다시 확인한다.

---

## 17. 개발 일정

2026년 8월 3일 월요일부터 시작하는 로컬 우선 일정이다. 호스팅 계약 전에는 fixture, 로컬 FastAPI, Android Emulator를 사용해 8주 동안 로컬 MVP를 완성한다. 호스팅과 Play 프로덕션 연동은 계약 이후 2주 이상의 별도 단계로 진행한다.

### 1주차(8/3~8/7) — 로컬 개발 기반

- [ ] Python, Android Studio, SDK/JDK 환경 점검
- [ ] monorepo 스캐폴드와 `.gitignore`, `.env.example`
- [ ] 로컬/운영 환경설정 분리 원칙과 ADR
- [ ] US/JP/KR 샘플 기사와 결과 fixture
- [ ] 백엔드·Android 기본 빌드와 CI

완료 기준: 새 PC에서도 문서대로 로컬 프로젝트를 빌드하고 테스트할 수 있음

### 2주차(8/10~8/14) — 데이터 계약과 로컬 API

- [ ] 모델/Schema와 JSON Repository
- [ ] 원자적 저장, 날짜 범위, 보관 정책
- [ ] issues/dates/status/config API와 테스트
- [ ] fixture 모드 배치와 Swagger 검증

완료 기준: `localhost:8000`에서 fixture 기반 전체 API 시연

### 3주차(8/17~8/21) — 수집과 정제

- [ ] Collector 인터페이스와 소스 어댑터
- [ ] 중복 제거와 국가별 병렬 수집
- [ ] `fixture/live/mixed` 데이터 모드
- [ ] mock 테스트와 출처 이용조건 기록

완료 기준: fixture 3개국과 허용된 실제 소스 최소 1개가 같은 계약으로 동작

### 4주차(8/24~8/28) — LLM과 이슈 집계

- [ ] 프롬프트, 구조화 출력, 묶음 처리, 캐시
- [ ] 클러스터링, TOP 5, 비용 기록
- [ ] LLM mock과 실제 API 어댑터 분리
- [ ] 근거 검증과 품질 샘플 리뷰

완료 기준: 국가별 서로 다른 TOP 5 JSON 생성

### 5주차(8/31~9/4) — 전체 배치와 웹 데모

- [ ] 전체 pipeline과 부분 성공
- [ ] 자동 리뷰, 보고서, lock, retry, retention
- [ ] 정적 웹 클라우드와 상태 처리
- [ ] Windows 로컬 실행 스크립트와 통합 테스트

완료 기준: 배치→API→웹 전체 흐름 검증

### 6주차(9/7~9/11) — Android 기반과 API 연결

- [ ] Compose 프로젝트와 화면 내비게이션
- [ ] debug API URL을 `10.0.2.2:8000`으로 주입
- [ ] 국가/날짜 탭, 네트워크 Repository
- [ ] debug 전용 HTTP 허용, release HTTPS 강제

완료 기준: Android Emulator가 로컬 FastAPI 결과를 표시

### 7주차(9/14~9/18) — Android UI와 오프라인

- [ ] 결정적 이슈 클라우드와 TOP 5 상세
- [ ] Room 캐시와 오프라인 폴백
- [ ] 로딩, 부분 성공, 지연, 오류 상태
- [ ] 접근성과 다기기 UI 테스트

완료 기준: 네트워크를 끊어도 마지막 정상 결과 조회

### 8주차(9/21~9/25) — 로컬 MVP 안정화

- [ ] 전체 테스트, 성능, 오류 복구 검증
- [ ] 로컬 원클릭 실행 문서와 스크립트
- [ ] README, 아키텍처, 데모 이미지
- [ ] 호스팅 URL을 환경설정으로 주입하는 release 구성
- [ ] `v0.8.0-local-mvp` 태그 후보 준비

완료 기준: 호스팅 없이 PC+Emulator에서 전체 제품 흐름 재현

### 호스팅 계약 후 1주차 — 운영 배포

- [ ] VPS/도메인, nginx, TLS, systemd
- [ ] 운영 환경변수와 API URL 주입
- [ ] GitHub Actions 배포와 health/ready
- [ ] 7일 연속 자동 배치 관찰

완료 기준: 코드 로직 변경 없이 설정만으로 운영 환경 동작

### 호스팅 계약 후 2주차 이후 — Play 테스트와 출시

- [ ] 개인정보처리방침, Data Safety, 뉴스 앱 선언
- [ ] release AAB와 Play 내부/비공개 테스트
- [ ] 요구되는 테스터 기간 충족과 피드백 반영
- [ ] `v1.0.0`, GitHub Release, 단계적 출시

완료 기준: Play 링크, Live Demo, 공개 GitHub 제공

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
v0.6.0 웹 데모
v0.7.0 Android 핵심 UI
v0.8.0 오프라인과 안정화
v0.9.0 VPS와 Play 비공개 테스트
v1.0.0 첫 공개 릴리스
```

---

## 19. 출시 게이트

- [ ] 수집이 특정 주제 검색에 편향되지 않음
- [ ] 최소 2개국 운영 소스 이용조건 확인
- [ ] 7일 연속 자동 배치 결과 확보
- [ ] 한 국가 실패 시 다른 국가 결과 유지
- [ ] LLM 결과에 없는 기사/표현이 포함되지 않음
- [ ] API 200/400/404/503 검증
- [ ] Android 오프라인과 캐시 복구 검증
- [ ] release AAB가 운영 API에서 동작
- [ ] 개인정보처리방침, 문의, 출처, 발행일 표시
- [ ] GitHub에 비밀키와 운영 데이터가 없음
- [ ] VPS 롤백 검증
- [ ] Play 선언과 테스트 요건 충족
- [ ] README에서 실제 앱/웹/설계/테스트 확인 가능

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
| VPS 장애 | health monitor, systemd, 캐시, 롤백 |
| Play 심사 지연 | 정책 자료 선제 준비와 일정 버퍼 |
| 공개 저장소 키 유출 | `.gitignore`, secret scan, 키 회전 |

---

## 21. 최종 산출물

- [ ] 통합 명세, 화면/기능/아키텍처 설계서와 ADR
- [ ] 데이터·출처 정책과 API 명세
- [ ] Python 배치와 FastAPI
- [ ] Android 앱과 웹 데모
- [ ] 자동 테스트와 CI/CD
- [ ] 배포 스크립트, nginx, systemd
- [ ] 운영 런북과 장애 보고서 예시
- [ ] 개인정보처리방침과 문의 페이지
- [ ] Google Play 등록 자료
- [ ] README, 데모 이미지, GitHub Release

---

## 22. 최종 정의

> 국가별 이슈 클라우드는 미국·일본·한국의 경제뉴스를 국가별로 독립 수집하고, LLM으로 각 국가 내부의 유사한 기사 표현을 이슈 단위로 묶은 뒤, 고유 기사 수와 매체 다양성에 따라 국가별 TOP 5를 계산해 클라우드 형태로 보여주는 Android 및 웹 애플리케이션이다. 결과에는 실제 출처와 표본 수를 제공하며, 배치 실패·오프라인·외부 API 비용과 같은 운영 문제를 명시적으로 처리한다.
