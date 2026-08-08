# 開発進捗状況

| 項目 | 現在状態 |
|---|---|
| 現在目標 | v2運用source coverage補完 |
| 状態 | source計測・公式RSS補完とNewsData.io US/JP adapter・限定実接続完了 |
| 基準branch | `main` |
| 作業branch | `codex/v2-source-coverage` |
| 最終完了commit | `66e9c2f` — keyword Pages v2 PR #22 Rebase and merge |
| 全体検証 | PASS — Python 103件・全体coverage 89%・Web 9件・Pages v2 artifact・Ruff・mypy・Secret・仕様同期 |
| 次作業 | NewsData.io日次上限reset後にPages live gate全体を1回再検証 |

## v1.0公開準備の進行結果

- 公開Pagesで3か国切替、TOP5、tile・cloud切替、詳細dialog、関連記事20件linkを確認し、console errorがないことを確認した。
- 配布成否に関係なく現在の公開HTMLと`data/v2`契約を確認する`public-smoke` jobとretry可能な検査scriptを追加した。
- 予約・手動retry・配布・Secret事故対応と7日運用gateを韓日運用Runbookと観察表へ整理した。
- 7日連続自動batch証跡は時間経過が必要なrelease gateとして未完了を維持する。
- JST日付別の過去24時間計算と手動遡及用`--skip-rss --single-attempt`を追加し、8/2～8の実GDELT・NAVER経路を確認した。
- raw・重複除去・最終選択件数とsource別寄与を原文なしで`data/runtime/collection-diagnostics.json`へatomicに記録する。
- 公式無料sourceのCensus経済指標RSSとBEA news release RSSを米国補助収集へ追加した。
- 日本財務省・統計局の公式RSSを追加し、RSS 1.0/RDFのdefault namespace parseを実装した。直近168時間の限定実接続で財務省51件・統計局5件を収集した。
- 韓国政策ブリーフィングRSSは2026-07-01の終了案内を確認し、追加しなかった。
- GDELT・NAVERのscope/domain/date/duplicate/limit段階別除外件数とNAVER上位除外domainをlocal診断へ追加した。
- NAVER許可domain `2026-08-08.v3`限定実接続で500件中103件を採用し、診断用の別ledgerは25/300回となった。
- GDELT最小requestでHTTP 429を再現し、安全なerror分類と同一batchの429 circuit breakerを追加した。
- NewsData.io無料Latest APIを米国・日本の`business`補完sourceとして追加し、国別目標・上限150件、日40回・月1,200回hard stopと有料自動移行禁止を適用した。初回の直近24時間限定実接続でUS・JP各100件を確保した。
- 初回live gate全体はNewsData.io raw US/JP各100件でも重複・媒体偏重適用後US 89・JP 73、NAVER KR 95となり、安全に公開を停止した。品質基準は維持し、NewsData.io目標を150件へ調整して、NAVER許可媒体v4を根拠のある主要媒体で補完した。日次上限保護のため同日の追加live retryは行わない。
- 次回live 1回で偏重原因を確認できるよう、診断Schema 1.1へsource別採用媒体集計を追加した。記事title・URL・ID・Secretは記録しない。
- 7日すべて3か国100件未満で公開が安全に停止した。最大は8/3 US 34・KR 90、8/5 JP 26・KR 90で、NAVERは40/300回を使用した。

## keyword news v2決定

- Schema 2.0、`/api/v2/keywords`、`data/v2`、v1独立Repositoryを追加し、v1契約を維持した。
- Web標準DataSourceをv2へ移行し、国別TOP 5のclickで関連記事最大20件を表示する。
- main pushは国別120件fixture TOP 5を配布し、予約実行は直前24時間のGDELT・RSS・NAVER結果が基準通過時だけ既存正常Pagesを置換する。

- 言語別の決定的複合名詞候補抽出、国別一般語・叙述語除外、入力候補限定の同義語統合を実装した。
- 国別最低100件を強制し、document frequency・媒体多様性・最新時刻・IDでTOP 5を決定し、関連記事IDを最大20件接続する。
- 国別120件fixtureで期待複合名詞5件、決定性、一般語除外、国分離、原文根拠接続を検証する。

- GDELT DOC APIを国別主source、既存公共RSS/APIを補助sourceへ変更する。
- 重複排除後の国別150件を目標、最大250件、正常100件以上、部分成功50～99件とする。
- 言語別名詞・複合名詞抽出とstopword除外後、LLMは同義語・表示名統合だけを行う。
- document frequencyと媒体多様性でkeyword TOP 5を決め、keyword別関連記事を最大20件提供する。
- 既存v1の意味を維持し、Schema/API/静的JSONをv2として一緒に移行する。
- 詳細根拠と実装順序は`docs/adr/ADR-0001-keyword-news-pipeline.md`に従う。
- 初回運用はGDELT・NAVER無料枠・公式RSS/APIだけを使い、有料news APIと外部有料LLM資格情報は登録しない。
- GDELTと公式RSSにSecretは不要で、韓国news補完時だけ`NAVER_CLIENT_ID`、`NAVER_CLIENT_SECRET`が必要となる。
- NAVER利用policyは日300回・月9,000回hard stop、50%・80%通知、有料超過利用無効で確定し、code設定と停止guardを追加した。account全体の停止と通知はConsoleで同じ値を設定する必要がある。
- NAVER news収集adapter、韓国経済query巡回、承認済み媒体の原文domain filter、認証header、HTML title整形、永続利用量ledgerを実装した。v1保護のため`--enable-naver`明示実行時だけ有効化する。
- NAVER制限付き実接続では`経済`1回で承認domain 5件・6記事、5 queryで承認domain 7件・重複排除後31記事を確保した。NAVER単独100件には未達のため、GDELT・RSS合算と根拠あるquery・allowlist補完が必要となる。
- 完了review Highで無料policy再確認日後も呼出可能なriskを検出し、再確認期限切れ時は認証request前に自動停止するよう修正した。
- GDELT JSON adapter、query version、国別120件fixture、250件上限、媒体別20%/30件制限を実装した。
- 制限付きlive検証は無料endpointの429と実媒体coverageによりUS 43件・JP/KR errorとなり、理由付きpartialとして記録した。先行呼出ではKR raw 250件・4媒体を確認した。
- 既存v1 Pagesを保護するため`publish-live --enable-gdelt`を明示した評価時だけGDELTを使い、v2移行前の予約batchはRSSを維持する。

## 3週目の進行結果

- 米国はFederal Reserve・BLS RSS、日本はMETI Atom・BOJ RSS、韓国は韓国銀行RSSを有効候補として確定した。
- BEA・e-Statは登録情報が必要なため標準無効として記録した。
- 2件の条件付きAPIについて、利用者登録、Secret保管、adapter実装、有効化checklistを韓日guideとして作成した。
- KDIの代わりに登録不要の金融委員会報道資料・報道説明RSSと中小ベンチャー企業部報道資料RSSを有効候補へ反映した。
- 公式RSS実接続で米国7件・日本28件・韓国27件とPages JSON生成を検証した。
- BLSは自動request 403、METIは6月以降未更新を確認し、状態が変わるまで無効へ切り替えた。
- source別許可field、利用条件確認日、90日後の再確認日を設定へ反映した。
- RSS 2.0とAtomを同じCollectorで処理し、不正な日付entryだけを分離するよう補完した。
- C案tile標準・A案cloud切替、国・日付選択、原文詳細、cache復旧とresponsive accessibility画面を実装した。
- 毎日09:00 JST/KSTに実RSSを検証・公開するPages workflowと、失敗時に既存配布を維持する構造を実装した。
- 10:00・12:00 JST/KST補完scheduleと日付別live-attempt cache markerを追加した。外部収集段階へ入った日は成否に関係なく自動live再実行を停止し、収集前段階の失敗だけを補完する。
- merge pushが不足したlive RSSを実行してbuild失敗と当日試行権消費を起こす問題を修正した。`main` pushはfixtureを配布し、予約・明示的な手動実行だけがlive modeを使う。
- 出典・保存・privacy・問い合わせpageとlocal fixture preview手順を追加した。
- 完了review High 2件であるPages出力path保護と補助RSS順位weightを修正・再検証した。
- PR #9 merge後、GitHub Runnerの一時pathが安全検査で遮断されたため、repository内の`dist/site`をPages artifact出力pathとして使うmerge後修正を完了した。
- 公開画面の初期data loading失敗状態で国buttonがnull結果をrenderしていた問題を防止し、再試行UIとDOM動作testを追加した。
- PR #11初回CIで`jsdom`依存関係の未導入を確認し、標準CIにNode.jsと`npm ci`手順を追加した。
- 実browserの`window.fetch`呼出contextを維持し、favicon 404を解消するmerge後修正を進める。
- 確定app sampleの白・blue視覚体系と情報構造をresponsive Webへ適用する。
- `deploy-pages`が設定値に関係なく10分に制限されることを実行logで確認し、deploy jobを10分へ戻して、queue timeout後に時間を置いた手動再試行1回の方針へ訂正する。
- PR #15の新しい`main` SHA配布も10分間`deployment_queued`の後にcancelされ、同一SHAの手動再実行は即時`Deployment cancelled`で終了した。cancel済みPages配布IDを繰り返し使わないよう、文書変更を新SHAとしてmergeし、一度だけ再配布する。

## 2週目の進行結果

- 実providerを注入できる構造化LLM client境界と決定的mock extractorを実装した。
- 入力article ID・根拠表現・国境界をコードで検証し、hallucinationと国混在を遮断する。
- 国内類似labelを統合し、記事数・媒体数・最新時刻・issue ID順でTOP 5を決定する。
- 30秒timeout伝達、最大2回retry、内容hash cache、token・cost記録と月USD 10上限を実装した。
- 3か国pipeline、国別失敗分離、最低2か国公開、dry-run、重複実行lockを実装した。
- 検証済み直近7日JSONを既存正常siteとatomicに交換するstatic publisherを実装した。
- `StaticJsonDataSource`と後続`ApiDataSource`が同一Schemaを検証するWeb基盤を追加した。
- masking済みlocal障害reportとfixture→検証済み静的JSON統合CLIを実装した。

## 目標2の進行結果

- Pydantic v2ベースのissue result Schemaと国・状態enumを実装した。
- JSON Repositoryの日付別・最新取得と直近日付検索を実装した。
- 3か国必須、timezone付き時刻、HTTPS URL、順位・比率・記事数、追加field拒否規則を検証する。
- 正常取得、file不在、破損JSON、日付範囲、未知fileの分離をtestした。
- 日付resultと`latest.json`のatomic保存、当日を含む7日保管・期限切れ削除を実装した。
- `/api/v1`の全取得・状態・設定・health・ready endpointと400/404/503 error mappingを実装した。
- 目標2実装は完了し、1週目最終commitには目標3の収集・整形まで含める。

## 目標3の進行結果

- 共通Collector契約の下にJSON fixture adapterと注入式HTTPS RSS adapterを実装した。
- tracking parameter除去URL、正規化title、6時間以内かつ0.92以上のtitle類似度で国内重複を排除する。
- US/JP/KRを並列収集し、1か国・1 sourceの失敗を他国resultから分離する。
- `fixture`、`live`、`mixed`実行modeを支援し、mixedはlive結果がない場合fixtureへfallbackする。
- 匿名化した3か国article fixtureと外部networkを呼ばないintegration testを追加した。

## 完了済み目標

- 目標1 — 環境とプロジェクト骨格
  - 完了日：2026-08-03
  - PR：#5
  - `main` commit：`fb1fa04`
  - 検証：Ruff、mypy strict、pytest 4件、Secret検査、fixture smoke、GitHub CI PASS

## 目標1の進行結果

- `backend`、`android`、`frontend`、`config`、`deploy`、`sample-data`のmonorepo scaffoldを構成した。
- Python 3.12、FastAPI、Pydantic Settings、uvベースのbackend環境と`uv.lock`を構成した。
- 標準実行modeを`fixture`に固定し、外部API・LLM keyなしでも設定を読み込めるようにした。
- US/JP/KRを独立させたsample fixtureと検証testを追加した。
- PRと`main`で共通検証を実行する基本CIを追加した。
- ローカルPATHにuv・Python・Java・ADBはなかった。uv 0.11.32はGit除外対象の`.tools/`へ導入して検証した。Java・Android SDK導入は保留し、Android再開決定後のみ必要とする。

## 現在の決定事項

- GitHub Pages MVP期間は2026-08-03から2026-08-22までの3週間。
- 残り開発は週ごとに最終commit・branch・Draft PRを一つずつ使う。
- 週次reviewは土曜日固定ではなく、実装・test・文書・全検証の完了を検知した直後に実行する。
- 全commit subjectは`YYYY/MM/DD <type>: <English> | <한국어> | <日本語>`形式を使う。
- 現在の初回成果物はGitHub Pages URLのresponsive Webであり、GitHub Actions生成の静的JSONを`StaticJsonDataSource`で読む。
- FastAPIと`ApiDataSource`はローカル検証と後続VPS/EC2移行のため同じSchemaで維持する。
- Androidは削除せず、公開Web安定化後に選択的に再開する後続trackとして保留する。再開時はRetrofitを優先検討する。
- Python環境とpackageはuvで管理。
- 韓国語・日本語仕様は同じ作業とcommitで同期。
- method単位の説明コメントは日本語だけを使う。

## 既知の課題と外部依存

- 運用ニュースソースの利用条件をリリース前に確認する。
- LLM providerと実modelは目標4開始前に環境変数ベースadapterとして確定する。
- GitHub Pages公開にはVPS・EC2・別domain契約は不要である。
- VPS/EC2とdomainは後続API運用を選択した場合だけ契約・接続する。
- Google Play accountとAndroid SDKはAndroid後続track再開まで不要である。

## 目標完了時の更新項目

- 完了日とcommit SHA
- 実装範囲
- 実行した検証commandと結果
- 残る制約
- 次目標と最初の作業
