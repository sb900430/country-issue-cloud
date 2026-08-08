# 무료 뉴스 소스 환경변수 등록·활성화 설명서 / 無料ニュースソース環境変数登録・有効化ガイド

이 문서는 0원 운영을 전제로 GDELT DOC API, NAVER API HUB, 공식 RSS와 선택적 무료 통계 API에 필요한 환경변수와 등록 절차를 정의한다. GDELT와 공식 RSS에는 Secret이 필요 없고, 한국 뉴스 보강에는 NAVER 자격정보가 필요하다. BEA·e-Stat은 뉴스 수집원이 아니라 선택적 통계 보강용이다. 외부 유료 뉴스 API와 유료 LLM은 등록하지 않는다.

本書は0円運用を前提に、GDELT DOC API、NAVER API HUB、公式RSS、選択的な無料統計APIに必要な環境変数と登録手順を定義する。GDELTと公式RSSにSecretは不要で、韓国news補完にはNAVER資格情報が必要となる。BEA・e-Statはnews収集元ではなく、選択的な統計補完用とする。外部有料news APIと有料LLMは登録しない。

## 1. 한눈에 보는 준비 상태 / 準備状態一覧

| Source | 사용자가 해야 할 일 / 利用者が行うこと | 저장할 값 / 保存値 | 현재 코드 상태 / 現在のコード状態 | 활성화 조건 / 有効化条件 |
|---|---|---|---|---|
| GDELT DOC API (US/JP/KR) | 별도 등록 없음, attribution·이용조건 확인 / 登録不要、attribution・利用条件確認 | 없음 / なし | adapter·국가 query·120건 fixture 구현, v1 예약 실행은 기본 비활성 / adapter・国query・120件fixture実装、v1予約実行は標準無効 | v2 producer 전환 + 국가별 live 표본 재검증 / v2 producer移行 + 国別live sample再検証 |
| NAVER API HUB (KR) | NAVER Cloud 계정에서 application 등록 / NAVER Cloudアカウントでapplication登録 | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | 전용 adapter·사용량 차단 구현, 명시 flag로 활성 / 専用adapter・利用量停止を実装、明示flagで有効化 | Console 한도·알림 설정 + 제한 실연동 / Console上限・通知設定 + 制限付き実接続 |
| BEA API (US) | 이메일로 API key 신청, 약관 동의 / emailでAPI key申請、規約同意 | `BEA_API_KEY` | 전용 API adapter 미구현 / 専用API adapter未実装 | key 등록 + adapter·fixture·실연동 검증 / key登録 + adapter・fixture・実接続検証 |
| e-Stat API (JP) | 이용자 등록 후 Application ID 발급 / 利用者登録後Application ID発行 | `E_STAT_APP_ID` | 전용 API adapter 미구현 / 専用API adapter未実装 | app ID 등록 + 출처표시 + adapter·검증 / app ID登録 + 出典表示 + adapter・検証 |

등록과 승인은 사용자 명의·이메일·약관 동의가 필요하므로 Codex가 대신 수행하지 않는다. 비용 정책과 약관은 바뀔 수 있으므로 실제 등록일에 공식 페이지를 다시 확인한다.

登録と承認には利用者本人の氏名・email・規約同意が必要なため、Codexは代理で実施しない。料金方針と規約は変更される可能性があるため、実際の登録日に公式pageを再確認する。

## 1.1 GDELT 주 소스 전환 / GDELT主source移行

공식 자료: [GDELT Project](https://www.gdeltproject.org/), [DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)

- 국가별로 `sourcecountry`와 `sourcelang`을 함께 적용하고 직전 24시간 Article List를 최대 250건 요청한다.
- 경제 범위 query는 설정 파일에서 version 관리하며, 동일한 기준일에는 결정적으로 재현할 수 있어야 한다.
- 특정 기업·사건을 미리 검색어로 넣어 TOP 5를 유도하지 않고, 넓은 경제 주제 묶음과 제외어를 사용한다.
- 응답의 title, URL, domain/publisher, source country, language, publication time 등 공개 metadata만 수집한다.
- 기사 본문과 이미지를 대상 언론사에서 추가 crawl하지 않는다.
- URL·정규화 title·유사도 순으로 GDELT 내부 및 보조 RSS와 중복 제거한다.
- 국가별 중복 제거 후 150건을 목표로 하며 100건 이상을 정상, 50~99건을 부분 성공으로 처리한다.
- 공개 화면과 프로젝트 정보에 `Data source: GDELT Project`와 공식 site link를 표시한다.
- 호출 timeout, 제한된 1회 retry, query별 기사 수, 응답 지연과 HTTP 상태를 기록하되 원문 응답 전체는 log에 남기지 않는다.
- 무료 endpoint의 429를 줄이기 위해 국가 요청을 최소 60초 간격으로 직렬화하며, 현재 v1 예약 배치에서는 `--enable-gdelt`를 지정하지 않는다.

- 国別に`sourcecountry`と`sourcelang`を同時適用し、直前24時間のArticle Listを最大250件要求する。
- 経済範囲queryは設定fileでversion管理し、同じ基準日には決定的に再現可能とする。
- 特定企業・事件を事前に検索語へ入れてTOP 5を誘導せず、広い経済topic群と除外語を使う。
- responseのtitle、URL、domain/publisher、source country、language、publication timeなど公開metadataだけを収集する。
- 記事本文と画像を対象報道機関から追加crawlしない。
- URL・正規化title・類似度順でGDELT内部および補助RSSと重複排除する。
- 国別重複排除後150件を目標とし、100件以上を正常、50～99件を部分成功として扱う。
- 公開画面とproject情報に`Data source: GDELT Project`と公式site linkを表示する。
- request timeout、制限付き1回retry、query別記事数、response遅延、HTTP statusを記録し、raw response全体はlogへ残さない。
- 無料endpointの429を減らすため国requestを最低60秒間隔で直列化し、現在のv1予約batchでは`--enable-gdelt`を指定しない。

## 2. 공통 Secret 보관 절차 / 共通Secret保管手順

### 로컬 / Local

1. PowerShell에서 저장소 루트로 이동해 `Copy-Item backend/.env.example backend/.env`를 한 번 실행한다. 기존 `backend/.env`가 있으면 덮어쓰지 않는다.
2. `backend/.env`에 발급받은 값만 기록한다. GDELT와 RSS만 사용할 때는 Secret 값을 모두 비워 둬도 된다.
3. `backend/.env.example`에는 변수 이름과 빈 예시만 둔다.
4. 터미널 출력, daily report, review report, fixture, 생성 JSON에는 실제 값을 넣지 않는다.

```dotenv
APP_MODE=fixture
API_PREFIX=/api/v1
SERVICE_TIMEZONE=Asia/Tokyo
DATA_DIR=../data
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
NAVER_DAILY_REQUEST_LIMIT=300
NAVER_MONTHLY_REQUEST_LIMIT=9000
NAVER_USAGE_ALERT_THRESHOLD_1=50
NAVER_USAGE_ALERT_THRESHOLD_2=80
NAVER_PAID_OVERAGE_ENABLED=false
BEA_API_KEY=
E_STAT_APP_ID=
LLM_PROVIDER=mock
```

`APP_MODE=fixture`는 외부 호출 없는 기본값이다. 실제 무료 소스를 명시적으로 검증할 때만 `mixed` 또는 구현 완료 후 `live`를 사용한다. 현재 무료 운영에는 `NEWS_API_KEY`, `LLM_API_KEY`, `LLM_MODEL`이 필요하지 않다.

1. PowerShellでrepository rootへ移動し、`Copy-Item backend/.env.example backend/.env`を一度実行する。既存の`backend/.env`は上書きしない。
2. `backend/.env`には発行済みの値だけを記録する。GDELTとRSSだけを使う場合はSecret値を全て空にしてよい。
3. `backend/.env.example`には変数名と空の例だけを置く。
4. terminal出力、daily report、review report、fixture、生成JSONへ実値を含めない。

`APP_MODE=fixture`は外部呼出なしの標準値である。実際の無料sourceを明示的に検証するときだけ`mixed`、または実装完了後に`live`を使う。現在の無料運用では`NEWS_API_KEY`、`LLM_API_KEY`、`LLM_MODEL`は不要である。

### GitHub Actions 운영 / GitHub Actions本番

1. GitHub 저장소의 **Settings → Environments**에서 운영용 Environment를 만든다. 권장 이름은 `pages-production`이다.
2. 해당 Environment의 **Environment secrets → Add secret**에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`과 실제 사용하는 선택 변수만 등록한다.
3. 실제 데이터 생성 workflow에만 Environment를 연결한다. PR workflow와 fork workflow에는 Secret을 전달하지 않는다.
4. workflow에서 값을 출력하거나 공개 Pages artifact·JSON에 포함하지 않는다.
5. 노출이 의심되면 GitHub 값만 바꾸지 말고 제공기관에서 기존 key를 폐기·재발급한다.

1. GitHub repositoryの**Settings → Environments**で本番用Environmentを作成する。推奨名は`pages-production`とする。
2. そのEnvironmentの**Environment secrets → Add secret**から`NAVER_CLIENT_ID`、`NAVER_CLIENT_SECRET`と実際に使う選択変数だけを登録する。
3. 実data生成workflowだけにEnvironmentを接続する。PR workflowとfork workflowへSecretを渡さない。
4. workflowで値を出力せず、公開Pages artifact・JSONへ含めない。
5. 漏えいが疑われる場合はGitHub側の値だけでなく、提供機関で旧keyを失効・再発行する。

## 3. NAVER API HUB 등록 / NAVER API HUB登録

공식 자료: [NAVER API HUB](https://www.ncloud.com/product/applicationService/naverApiHub), [뉴스 검색 API](https://api.ncloud-docs.com/docs/naver-api-hub-search-news)

### 사용자가 수행할 절차 / 利用者が行う手順

1. NAVER Cloud Platform에 로그인하고 결제수단·이용약관 화면이 표시되면 무료 한도와 초과 과금 정책을 확인한다. 유료 자동 확장은 신청하지 않는다.
2. Console에서 **Services → Application Services → NAVER API HUB**로 이동한다.
3. 애플리케이션을 등록하고 **Search API → 뉴스 검색 결과 조회** 권한만 선택한다.
4. 애플리케이션 이름은 `Country Issue Cloud`, 사용 목적은 `비상업적 공개 포트폴리오의 한국 경제뉴스 키워드 분석`으로 기록한다.
5. 발급된 Client ID와 Client Secret을 비밀번호 관리 도구에 먼저 저장한 뒤 `backend/.env`에 아래와 같이 입력한다.

```dotenv
NAVER_CLIENT_ID=발급받은_Client_ID
NAVER_CLIENT_SECRET=발급받은_Client_Secret
```

1. NAVER Cloud Platformへloginし、決済手段・利用規約画面が表示された場合は無料枠と超過課金policyを確認する。有料自動拡張は申請しない。
2. Consoleの**Services → Application Services → NAVER API HUB**へ移動する。
3. applicationを登録し、**Search API → news検索結果照会**権限だけを選択する。
4. application名は`Country Issue Cloud`、利用目的は`非営利公開portfolioの韓国経済news keyword分析`と記載する。
5. 発行されたClient IDとClient Secretをpassword管理toolへ先に保存し、`backend/.env`へ上記の形式で入力する。

### 코드 활성화 절차 / Code有効化手順

NAVER 전용 수집 adapter는 v2 예약 `publish-keyword-live`에서 한국 경제뉴스 보강용으로 활성화된다. GitHub의 `pages-production` Environment에 두 Secret이 없으면 인증 요청 전에 실패하며, PR·fixture 검증에서는 호출하지 않는다.

1. 인증값을 `X-NCP-APIGW-API-KEY-ID`, `X-NCP-APIGW-API-KEY` header로 전달하고 log에서 마스킹한다.
2. 경제 주제 query를 순환하되 결과의 `originallink` domain을 승인된 한국 경제언론 allowlist로 제한한다.
3. 한 요청 최대 100건, 일일 자체 호출 상한을 설정하고 HTTP 429에서는 당일 추가 호출을 중단한다.
4. GDELT 결과와 URL·정규화 title·유사도로 중복 제거한다.
5. fixture·mock test 후 수동 실연동에서 기사량, 도메인 분포, 무료 한도와 오류 처리를 확인한다.
6. GitHub 운영 workflow에서는 `environment: pages-production`을 연결하고 PR workflow에는 Secret을 전달하지 않는다.
7. Console의 Application 목록에서 **한도 및 알림**을 열어 일별 한도 `300`, 월별 한도 `9000`을 저장하고 사용량 `50%`, `80%` 알림과 통보 대상을 활성화한다. 이 Console hard limit은 여러 실행 환경의 사용량을 합산하는 최종 차단선이다.
8. `NAVER_PAID_OVERAGE_ENABLED=false`를 유지한다. 무료 정책이 변경되어도 사용자 승인과 한·일 명세 변경 전에는 유료 초과 호출이나 자동 한도 증설을 적용하지 않는다.

NAVER専用収集adapterはv2予約`publish-keyword-live`で韓国経済news補完用として有効化する。GitHubの`pages-production` Environmentに2件のSecretがない場合は認証request前に失敗し、PR・fixture検証では呼び出さない。

1. 認証値を`X-NCP-APIGW-API-KEY-ID`、`X-NCP-APIGW-API-KEY` headerで渡し、logではmaskingする。
2. 経済topic queryを循環し、結果の`originallink` domainを承認済み韓国経済媒体allowlistに限定する。
3. 1 request最大100件、独自の日次呼出上限を設定し、HTTP 429では当日の追加呼出を停止する。
4. GDELT結果とURL・正規化title・類似度で重複排除する。
5. fixture・mock test後、手動実接続で記事数、domain分布、無料枠、error処理を確認する。
6. GitHub本番workflowでは`environment: pages-production`を接続し、PR workflowへSecretを渡さない。
7. ConsoleのApplication一覧から**上限および通知**を開き、日次上限`300`、月次上限`9000`を保存し、使用量`50%`、`80%`通知と通知対象を有効にする。このConsole hard limitを複数実行環境の利用量を合算する最終停止線とする。
8. `NAVER_PAID_OVERAGE_ENABLED=false`を維持する。無料policyが変更されても、利用者承認と韓日仕様変更前に有料超過呼出や自動上限拡張を適用しない。

## 4. BEA API 등록 / BEA API登録

공식 자료: [BEA API Key 신청](https://apps.bea.gov/api/signup/), [BEA API User Guide](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf)

### 사용자가 수행할 절차 / 利用者が行う手順

1. 공식 신청 페이지에서 이름, 소속, 유효한 이메일을 입력한다.
2. BEA API 이용약관을 읽고 동의한 뒤 신청한다.
3. 이메일로 받은 API key를 비공개 비밀번호 관리 도구에 먼저 보관한다.
4. 로컬은 `BEA_API_KEY`, GitHub 운영은 같은 이름의 Environment Secret으로 등록한다.
5. 신청 또는 key 문제는 BEA 안내 주소 `developers@bea.gov`로 문의한다.

1. 公式申請pageで氏名、所属、有効なemailを入力する。
2. BEA API利用規約を確認・同意して申請する。
3. emailで届いたAPI keyを非公開のpassword管理toolへ先に保存する。
4. localでは`BEA_API_KEY`、GitHub本番では同名のEnvironment Secretとして登録する。
5. 申請またはkeyの問題はBEA案内先`developers@bea.gov`へ問い合わせる。

### 코드 활성화 절차 / Code有効化手順

BEA API는 RSS가 아니므로 현재 RSS adapter에 URL만 추가해서는 동작하지 않는다. 다음 개발 작업으로 별도 BEA API adapter를 구현해야 한다.

1. API key를 BEA 요청의 `UserID` parameter로 전달하되 log와 오류 메시지에서 마스킹한다.
2. 필요한 dataset과 parameter를 명시적으로 제한하고 응답을 기존 Article/Issue Schema로 변환한다.
3. 실제 key를 쓰지 않는 fixture·mock test를 먼저 추가한다.
4. 수동 `workflow_dispatch` 또는 로컬 명시 옵션으로 소량 실연동을 1회 검증한다.
5. 응답 필드, attribution, 오류·timeout·rate 제한 처리를 확인한다.
6. 검증 후 `config/sources.example.yml`의 `bea_api`에 endpoint 정보를 추가하고 `terms_status: approved`, `enabled: true`, 실제 확인일과 90일 후 재검토일을 기록한다.

BEA APIはRSSではないため、現在のRSS adapterへURLだけを追加しても動作しない。次の開発作業として専用BEA API adapterを実装する必要がある。

1. API keyをBEA requestの`UserID` parameterとして渡し、logとerror messageではmaskingする。
2. 必要なdatasetとparameterを明示的に制限し、responseを既存Article/Issue Schemaへ変換する。
3. 実keyを使わないfixture・mock testを先に追加する。
4. 手動`workflow_dispatch`またはlocalの明示optionで少量実接続を1回検証する。
5. response field、attribution、error・timeout・rate制限処理を確認する。
6. 検証後、`config/sources.example.yml`の`bea_api`へendpoint情報を追加し、`terms_status: approved`、`enabled: true`、実確認日と90日後の再確認日を記録する。

## 5. e-Stat API 등록 / e-Stat API登録

공식 자료: [e-Stat API 기능 이용 가이드](https://www.e-stat.go.jp/api/api/api/index.php/api-info/api-guide), [이용자 사전등록](https://www.e-stat.go.jp/mypage/user/preregister), [이용약관](https://www.e-stat.go.jp/api/terms-of-use)

### 사용자가 수행할 절차 / 利用者が行う手順

1. e-Stat 사전등록 페이지에서 이메일 인증과 이용자 등록을 완료한다.
2. 로그인 후 **マイページ → API機能**에서 새 Application ID를 발급한다.
3. 애플리케이션 이름은 `Country Issue Cloud`, 설명은 비상업적 공개 포트폴리오와 일일 통계 이슈 생성 용도로 기재한다.
4. 아직 GitHub Pages URL이 없으면 e-Stat 안내에 따라 개발용 URL로 등록하고, 공개 URL 확정 후 같은 Application ID의 URL을 갱신한다.
5. 발급된 ID는 로컬 `E_STAT_APP_ID`와 GitHub Environment Secret에 등록한다. e-Stat은 Application ID를 최대 3개까지 발급할 수 있으므로 개발·운영 용도를 구분해 기록한다.

1. e-Stat事前登録pageでemail認証と利用者登録を完了する。
2. login後、**マイページ → API機能**から新しいApplication IDを発行する。
3. application名は`Country Issue Cloud`、説明には非営利公開portfolioと日次統計issue生成用途を記載する。
4. GitHub Pages URLが未確定ならe-Stat案内に従って開発用URLを登録し、公開URL確定後に同じApplication IDのURLを更新する。
5. 発行IDをlocalの`E_STAT_APP_ID`とGitHub Environment Secretへ登録する。e-StatはApplication IDを最大3件発行できるため、開発・本番用途を区別して記録する。

### 코드 활성화 절차 / Code有効化手順

1. `appId` query parameter를 log와 오류 메시지에서 마스킹하는 e-Stat 전용 API adapter를 구현한다.
2. 사용할 통계표 ID와 조회 범위를 allowlist로 제한한다. 전체 통계를 무차별 순회하지 않는다.
3. fixture·mock test, timeout, 재시도, 응답 Schema 검증을 추가한다.
4. 웹 화면과 생성 JSON에서 e-Stat 출처 및 원문 링크가 식별되도록 한다.
5. 소량 실연동으로 응답과 부하 제한을 확인한다. 공식 정책상 정해진 호출 횟수가 없더라도 자체 호출 상한과 backoff를 유지한다.
6. 검증 후 `e_stat_api`를 `terms_status: approved`, `enabled: true`로 변경하고 확인일·재검토일을 기록한다.

1. `appId` query parameterをlogとerror messageでmaskingするe-Stat専用API adapterを実装する。
2. 使用する統計表IDと取得範囲をallowlistで制限する。全統計を無差別に巡回しない。
3. fixture・mock test、timeout、retry、response Schema検証を追加する。
4. Web画面と生成JSONでe-Statの出典および原文linkを識別可能にする。
5. 少量実接続でresponseと負荷制限を確認する。公式方針に固定回数制限がなくても、独自の呼出上限とbackoffを維持する。
6. 検証後、`e_stat_api`を`terms_status: approved`、`enabled: true`へ変更し、確認日・再確認日を記録する。

## 6. 활성화 완료 체크리스트 / 有効化完了チェックリスト

- [ ] 공식 등록 또는 서면 승인을 완료하고 적용 약관 날짜를 확인했다. / 公式登録または書面承認を完了し、適用規約の日付を確認した。
- [ ] 실제 key·app ID는 `.env`와 GitHub Environment Secret에만 저장했다. / 実key・app IDを`.env`とGitHub Environment Secretだけへ保存した。
- [ ] Secret이 source branch, PR, log, fixture, Pages artifact에 없음을 secret scan으로 확인했다. / Secretがsource branch、PR、log、fixture、Pages artifactにないことをsecret scanで確認した。
- [ ] 해당 source용 adapter와 key 없는 fixture·mock test가 있다. / 該当source用adapterとkey不要のfixture・mock testがある。
- [ ] 허용 필드·출처표시·보관 기간·호출 제한을 코드와 설정에 반영했다. / 許可field・出典表記・保存期間・呼出制限をcodeと設定へ反映した。
- [ ] 명시적 소량 실연동과 오류·timeout·재시도 검증을 통과했다. / 明示的な少量実接続とerror・timeout・retry検証を通過した。
- [ ] `terms_checked_at`, `terms_review_due_at`, `terms_status`, `enabled`를 실제 상태로 갱신했다. / `terms_checked_at`、`terms_review_due_at`、`terms_status`、`enabled`を実状態へ更新した。
- [ ] `scripts/verify-all.ps1`과 주차 완료 review를 통과했다. / `scripts/verify-all.ps1`と週完了reviewを通過した。

활성화 뒤에도 약관 재검토일이 지나거나 제공기관이 정책·endpoint를 바꾸면 자동 수집을 중지하고 다시 확인한다. 기존 정상 Pages 결과는 새 수집 실패로 덮어쓰지 않는다.

有効化後も規約再確認日を過ぎた場合、または提供機関がpolicy・endpointを変更した場合は自動収集を停止して再確認する。既存の正常Pages結果を新規収集失敗で上書きしない。
