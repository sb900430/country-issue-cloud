# 開発進捗状況

| 項目 | 現在状態 |
|---|---|
| 現在目標 | 3週目 — responsive Web・GitHub Pages MVP |
| 状態 | 3週目実装・全検証完了 — 候補commit・完了review待ち |
| 基準branch | `main` |
| 作業branch | `codex/week-03-pages-mvp` |
| 最終完了commit | `be4af98` — 2週目PR #8 Rebase and merge |
| 全体検証 | PASS — Python 62件・Web 6件・Ruff・mypy・Secret・仕様・Pages artifact |
| 次作業 | 週完了候補commitと即時完了review |

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
- 毎日16:00 JST/KSTに実RSSを検証・公開するPages workflowと、失敗時に既存配布を維持する構造を実装した。
- 出典・保存・privacy・問い合わせpageとlocal fixture preview手順を追加した。
- 完了review High 2件であるPages出力path保護と補助RSS順位weightを修正・再検証した。

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
