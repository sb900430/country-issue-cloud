# 조건부 소스 등록·활성화 설명서 / 条件付きソース登録・有効化ガイド

이 문서는 키워드 중심 뉴스 파이프라인의 주 소스인 GDELT DOC API 운영 기준과 `config/sources.example.yml`에서 기본 비활성인 BEA API·e-Stat API의 안전한 활성화 절차를 정의한다. GDELT는 별도 Secret 없이 사용하지만 adapter·query·attribution 검증 전에는 운영 소스로 전환하지 않는다. 등록형 API도 자격정보 보관, adapter 구현, 제한된 실연동 검증까지 모두 통과한 뒤 활성화한다.

本書は、keyword中心news pipelineの主sourceであるGDELT DOC APIの運用基準と、`config/sources.example.yml`で標準無効のBEA API・e-Stat APIを安全に有効化する手順を定義する。GDELTはSecret不要だが、adapter・query・attribution検証前に本番sourceへ切り替えない。登録型APIも資格情報保管、adapter実装、制限付き実接続検証を全て通過した後に有効化する。

## 1. 한눈에 보는 준비 상태 / 準備状態一覧

| Source | 사용자가 해야 할 일 / 利用者が行うこと | 저장할 값 / 保存値 | 현재 코드 상태 / 現在のコード状態 | 활성화 조건 / 有効化条件 |
|---|---|---|---|---|
| GDELT DOC API (US/JP/KR) | 별도 등록 없음, attribution·이용조건 확인 / 登録不要、attribution・利用条件確認 | 없음 / なし | 전용 adapter 미구현 / 専用adapter未実装 | 국가 filter·fixture·100건 이상 실연동·출처표시 검증 / 国filter・fixture・100件以上実接続・出典表示検証 |
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

- 国別に`sourcecountry`と`sourcelang`を同時適用し、直前24時間のArticle Listを最大250件要求する。
- 経済範囲queryは設定fileでversion管理し、同じ基準日には決定的に再現可能とする。
- 特定企業・事件を事前に検索語へ入れてTOP 5を誘導せず、広い経済topic群と除外語を使う。
- responseのtitle、URL、domain/publisher、source country、language、publication timeなど公開metadataだけを収集する。
- 記事本文と画像を対象報道機関から追加crawlしない。
- URL・正規化title・類似度順でGDELT内部および補助RSSと重複排除する。
- 国別重複排除後150件を目標とし、100件以上を正常、50～99件を部分成功として扱う。
- 公開画面とproject情報に`Data source: GDELT Project`と公式site linkを表示する。
- request timeout、制限付き1回retry、query別記事数、response遅延、HTTP statusを記録し、raw response全体はlogへ残さない。

## 2. 공통 Secret 보관 절차 / 共通Secret保管手順

### 로컬 / Local

1. 저장소에 커밋되지 않는 `backend/.env`에 다음 값 중 발급받은 값만 기록한다.
2. `backend/.env.example`에는 변수 이름과 빈 예시만 둔다.
3. 터미널 출력, daily report, review report, fixture, 생성 JSON에는 실제 값을 넣지 않는다.

```dotenv
BEA_API_KEY=
E_STAT_APP_ID=
```

1. repositoryへcommitされない`backend/.env`に、発行済みの値だけを記録する。
2. `backend/.env.example`には変数名と空の例だけを置く。
3. terminal出力、daily report、review report、fixture、生成JSONへ実値を含めない。

### GitHub Actions 운영 / GitHub Actions本番

1. GitHub 저장소의 **Settings → Environments**에서 운영용 Environment를 만든다. 권장 이름은 `pages-production`이다.
2. 해당 Environment의 **Environment secrets → Add secret**에서 `BEA_API_KEY`, `E_STAT_APP_ID` 등 필요한 값만 등록한다.
3. 실제 데이터 생성 workflow에만 Environment를 연결한다. PR workflow와 fork workflow에는 Secret을 전달하지 않는다.
4. workflow에서 값을 출력하거나 공개 Pages artifact·JSON에 포함하지 않는다.
5. 노출이 의심되면 GitHub 값만 바꾸지 말고 제공기관에서 기존 key를 폐기·재발급한다.

1. GitHub repositoryの**Settings → Environments**で本番用Environmentを作成する。推奨名は`pages-production`とする。
2. そのEnvironmentの**Environment secrets → Add secret**から`BEA_API_KEY`、`E_STAT_APP_ID`など必要な値だけを登録する。
3. 実data生成workflowだけにEnvironmentを接続する。PR workflowとfork workflowへSecretを渡さない。
4. workflowで値を出力せず、公開Pages artifact・JSONへ含めない。
5. 漏えいが疑われる場合はGitHub側の値だけでなく、提供機関で旧keyを失効・再発行する。

## 3. BEA API 등록 / BEA API登録

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

## 4. e-Stat API 등록 / e-Stat API登録

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

## 5. 활성화 완료 체크리스트 / 有効化完了チェックリスト

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
