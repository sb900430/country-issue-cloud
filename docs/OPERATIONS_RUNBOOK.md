# 국가별 이슈 클라우드 운영 런북 / 国別イシュークラウド運用Runbook

## 한국어

### 운영 소스 확인

- 미국 공식 보조 소스는 Federal Reserve와 함께 Census 경제지표 RSS 및 BEA 뉴스 릴리스 RSS를 사용한다.
- 일본 공식 보조 소스는 일본은행과 함께 재무성 신착 RSS 및 통계국 신착 RSS를 사용한다.
- Census·BEA 피드는 등록이나 Secret이 필요 없으며 제목·요약·원문 링크·발행 시각만 처리한다.
- 재무성·통계국 피드도 등록이나 Secret이 필요 없으며, 일본 금융청 영문 RSS는 일본어 분석 혼합을 막기 위해 사용하지 않는다.
- NewsData.io는 미국·일본 `business` 보강에만 사용하며 `NEWSDATA_API_KEY`를 `pages-production` Environment에서 주입한다. 애플리케이션 한도는 일 40회·월 1,200회이고 유료 초과 사용은 금지한다.
- 대한민국 정책브리핑 RSS는 2026-07-01 서비스 중단 공지에 따라 활성 소스로 추가하지 않는다.
- 실제 기사 수 기여도는 `data/runtime/collection-diagnostics.json`의 소스별 건수로 확인한다. 이 파일은 로컬 런타임 전용이며 Git과 Pages artifact에 포함하지 않는다.

### 운영 범위

- 공개 서비스: `https://sb900430.github.io/country-issue-cloud/`
- 운영 workflow: `Publish Country Issue Cloud Pages`
- 기본 예약: 매일 09:00 JST/KST, 보충 확인 10:00·12:00
- 공개 데이터: `data/v2/latest.json`, 날짜별 JSON, `dates.json`
- 현재 운영은 GitHub Pages만 포함하며 VPS/EC2와 Android는 보류한다.

### 매일 확인

1. Pages workflow의 당일 최초 live 실행 여부와 결론을 확인한다.
2. `public-smoke` job이 현재 공개 HTML과 Schema 2.0 데이터를 통과했는지 확인한다.
3. 공개 화면에서 날짜, 세 국가, 국가별 기사 수와 TOP5를 확인한다.
4. 실패한 국가는 workflow log의 오류 유형과 수집 기사 수만 기록한다. 원문 응답과 인증 header는 저장하지 않는다.
5. 결과를 `docs/operations/BATCH_OBSERVATION.md`에 한 줄로 기록한다.

### 수동 실행

GitHub Actions에서 `Publish Country Issue Cloud Pages`의 **Run workflow**를 선택한다.

- 일반 재현: `data_mode=fixture`
- 당일 live 미실행: `data_mode=live`, `force_live_retry=false`
- 외부 호출이 이미 시작된 날: 자동 재시도하지 않는다.
- 원인을 확인하고 사용자가 호출량 소비를 승인한 경우에만 `force_live_retry=true`를 한 번 사용한다.

### 실패 대응

| 상황 | 조치 |
|---|---|
| build 전 실패 | 10:00·12:00 보충 실행을 기다리거나 fixture로 코드 경로만 확인 |
| live 수집 partial/failed | 기존 정상 Pages 유지 확인, 국가별 기사 수·오류 유형 기록 |
| deploy 실패 | 현재 공개 URL smoke 확인, 같은 SHA 반복 재배포 금지, 새 수정 PR 사용 |
| public smoke 실패 | `latest.json`, `dates.json`, HTML 순으로 확인하고 Pages 상태 확인 |
| Secret 의심 | workflow 중단, 키 폐기·회전, GitHub Secret Scanning 결과 확인 |

### 7일 운영 게이트

- 서로 다른 JST 날짜 7일의 예약 실행 결과를 기록한다.
- 성공 여부와 별개로 외부 수집 시도, 공개 데이터 날짜, 국가별 기사 수, 기존 Pages 유지 여부를 남긴다.
- 세 국가 모두 100건·TOP5를 충족한 날만 live 공개 성공으로 계산한다.
- 7일이 채워지기 전에는 출시 게이트를 완료 처리하지 않는다.

### 초기 소급 점검

- 운영 전 전체 경로 확인은 날짜별 `publish-keyword-live --target-date YYYY-MM-DD --lookback-hours 24 --skip-rss --single-attempt`로 실행할 수 있다.
- `--skip-rss`와 `--single-attempt`는 과거 피드 보존과 장시간 retry를 피하기 위한 수동 점검 옵션이며 예약 workflow에서는 사용하지 않는다.
- 결과는 Git 제외 로컬 경로에 저장하고 실제 Pages를 교체하지 않는다.

## 日本語

### 運用source確認

- 米国公式補助sourceはFederal Reserveに加えて、Census経済指標RSSとBEA news release RSSを使う。
- 日本公式補助sourceは日本銀行に加えて、財務省新着RSSと統計局新着RSSを使う。
- Census・BEA feedは登録やSecretが不要で、title・summary・原文link・公開時刻だけを処理する。
- 財務省・統計局feedも登録やSecretが不要で、日本金融庁の英語RSSは日本語分析への混在を防ぐため使用しない。
- NewsData.ioは米国・日本の`business`補完だけに使用し、`NEWSDATA_API_KEY`を`pages-production` Environmentから注入する。application上限は日40回・月1,200回で、有料超過利用は禁止する。
- 韓国政策ブリーフィングRSSは2026-07-01のservice終了案内によりactive sourceへ追加しない。
- 実際の記事数への寄与は`data/runtime/collection-diagnostics.json`のsource別件数で確認する。このfileはlocal runtime専用で、GitとPages artifactへ含めない。

### 運用範囲

- 公開service：`https://sb900430.github.io/country-issue-cloud/`
- 運用workflow：`Publish Country Issue Cloud Pages`
- 標準schedule：毎日09:00 JST/KST、補完確認10:00・12:00
- 公開data：`data/v2/latest.json`、日付別JSON、`dates.json`
- 現在の運用はGitHub Pagesだけを対象とし、VPS/EC2とAndroidは保留する。

### 毎日の確認

1. Pages workflowの当日最初のlive実行有無と結論を確認する。
2. `public-smoke` jobが現在の公開HTMLとSchema 2.0 dataを通過したか確認する。
3. 公開画面で日付、3か国、国別記事数、TOP5を確認する。
4. 失敗国はworkflow logのerror種別と収集記事数だけを記録する。raw responseと認証headerは保存しない。
5. 結果を`docs/operations/BATCH_OBSERVATION.md`へ一行で記録する。

### 手動実行

GitHub Actionsで`Publish Country Issue Cloud Pages`の**Run workflow**を選択する。

- 通常再現：`data_mode=fixture`
- 当日live未実行：`data_mode=live`、`force_live_retry=false`
- 外部呼出し開始済みの日：自動再試行しない。
- 原因確認後、利用者が呼出量消費を承認した場合だけ`force_live_retry=true`を一度使う。

### 失敗対応

| 状況 | 対応 |
|---|---|
| build前失敗 | 10:00・12:00の補完を待つかfixtureでcode pathだけを確認 |
| live収集partial/failed | 既存正常Pages維持を確認し、国別記事数・error種別を記録 |
| deploy失敗 | 現在の公開URLをsmoke確認し、同一SHAの反復再配布を避けて修正PRを使う |
| public smoke失敗 | `latest.json`、`dates.json`、HTMLの順に確認しPages状態を確認 |
| Secret疑い | workflow停止、key失効・rotation、GitHub Secret Scanning結果確認 |

### 7日運用gate

- 異なるJST日付7日分の予約実行結果を記録する。
- 成否に関係なく外部収集試行、公開data日付、国別記事数、既存Pages維持有無を残す。
- 3か国すべてが100件・TOP5を満たした日だけlive公開成功として数える。
- 7日分が揃う前にrelease gateを完了扱いしない。

### 初回遡及確認

- 運用前の全経路確認は日付別に`publish-keyword-live --target-date YYYY-MM-DD --lookback-hours 24 --skip-rss --single-attempt`で実行できる。
- `--skip-rss`と`--single-attempt`は過去feed保持と長時間retryを避ける手動確認optionであり、予約workflowでは使わない。
- 結果はGit除外local pathへ保存し、実Pagesを置換しない。
