# 開発進捗状況

| 項目 | 現在状態 |
|---|---|
| 現在目標 | 目標2 — データ契約とローカルAPI |
| 状態 | 目標1完了、目標2開始前 |
| 基準branch | `main` |
| 予定作業branch | `codex/milestone-02-local-api` |
| 最終完了commit | `fb1fa04` — 目標1 |
| 全体検証 | merge済み`main`の全検証・fixture smoke・CI PASS |
| 次作業 | 2026-08-04 data model、Schema、JSON Repository実装 |

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
- ローカルPATHにuv・Python・Java・ADBはなかった。uv 0.11.32はGit除外対象の`.tools/`へ導入して検証し、Java・Android SDKはAndroid目標開始前にinstallが必要である。

## 現在の決定事項

- ローカルMVP期間は2026-08-03から2026-08-29までの4週間。
- 8目標ごとに最終commitを一つ作成。
- 各目標は専用branchとDraft PRを通して`main`へ反映する。
- 全commit subjectは`YYYY/MM/DD <type>: <English> | <한국어> | <日本語>`形式を使う。
- Android HTTPはRetrofitを利用。
- Python環境とpackageはuvで管理。
- 韓国語・日本語仕様は同じ作業とcommitで同期。
- method単位の説明コメントは日本語だけを使う。

## 既知の課題と外部依存

- 運用ニュースソースの利用条件をリリース前に確認する。
- LLM providerと実modelは目標4開始前に環境変数ベースadapterとして確定する。
- VPS、domain、Google Play accountは未契約・未接続。

## 目標完了時の更新項目

- 完了日とcommit SHA
- 実装範囲
- 実行した検証commandと結果
- 残る制約
- 次目標と最初の作業
