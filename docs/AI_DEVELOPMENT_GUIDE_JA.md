# AI開発ガイド

本書は、AIと高速に開発しながらスコープ逸脱、検証漏れ、コンテキスト消失を防ぐための実行規則である。製品要件は`PROJECT_SPEC.md`と`PROJECT_SPEC_JA.md`に従う。

## 1. 固定技術選定

| 領域 | 選定 |
|---|---|
| Python環境・package | `uv`、`pyproject.toml`、lockfileをcommit |
| API | FastAPI、Pydantic v2系 |
| Web（現在優先） | Semantic HTML/CSS/Vanilla JS、Fetch API、npmベースの検査・test |
| Web状態・保存 | JavaScript状態module、localStorage、Cache APIまたはIndexedDB |
| data access | `IssueDataSource`、標準Static JSON、後続FastAPI adapter |
| 初回運用 | GitHub Actions schedule/workflow_dispatch + GitHub Pages artifact |
| 後続運用 | VPS/EC2 + FastAPI、DataSource設定だけ切替 |
| Android（保留） | 再開時にRetrofit、Kotlinx Serialization、ViewModel、Flow、Room、DataStore、Hiltを再検証 |
| 日時 | サーバーはUTC保存、`Asia/Tokyo`表示 |
| ニュース収集目標 | NewsData.io・NAVERと公共RSS/API、GDELTは429解消まで保留、国別150件目標・250件上限 |
| keyword分析 | 構成単語・複合名詞保持 → 国別YAML禁止語 → local多言語embedding限定統合・記事凝集度 → 2%・3件・正規化2媒体gate → 一般語・重複イシュー除外 → 品質3～5件順位 |
| keyword表示翻訳 | 順位確定後にversion管理された完全一致辞書でUS・JPの`label_ko`を生成。KR・未登録表現は原文fallback、外部翻訳APIは標準禁止 |

正確なversionはscaffold時点の公式安定版を確認して固定し、lockfileまたはversion catalogへ記録する。依存関係を無断追加せず、標準機能で解決困難な場合だけADRへ導入理由を残す。

## 2. AI作業依頼契約

```md
## 作業目標
利用者が確認できる結果

## 作業範囲
変更可能な機能とdirectory

## 対象外
今回変更しない項目

## 完了条件
- 機能要件
- 必須test
- 文書同期

## 検証command
実行するcommandと期待結果

## 週次commit
開発週と最終commit message
```

不足項目は仕様と現コードから安全に判断できる範囲でAIが補完する。費用、外部契約、公開範囲、資格情報、復元困難な変更など利用者判断が必要な場合は実行前に質問する。

## 3. 作業手順

1. `AGENTS.md`、両仕様書、`docs/DEVELOPMENT_STATUS.md`を読む。
2. `main`を最新化し、対象週の`codex/week-*` branchを作る。
3. `git status`で利用者変更を確認し保護する。
4. 要件、影響ファイル、検証基準を確認する。
5. 最小の完結単位で実装し、関連testを実行する。
6. 仕様へ影響する場合は韓国語・日本語版を同時更新する。
7. `scripts/verify-all.ps1`を実行する。
8. 当日に開発作業があれば`docs/daily/YYYY-MM-DD.md`の日次報告を作成し、開発状態文書を更新する。
9. WIPをsquashして週次commit一つに整理する。
10. 週次branchをpushし、`main`対象のDraft PRを一つ作成する。
11. CIとreview通過後にReadyへ変更し、**Rebase and merge**でmergeする。
12. 最新`main`へ切り替え、`scripts/verify-all.ps1`と利用可能なローカルsmoke testを再実行する。
13. merge後検証が成功した場合だけ対象週を完了扱いとし、次週branchを作る。

## 4. 日次開発レポート

- 開発作業を行った日の終了時に`docs/daily/TEMPLATE.md`から`docs/daily/YYYY-MM-DD.md`を作成する。
- 一つのファイルに同じ意味の韓国語・日本語sectionを両方記述する。
- 日付は`Asia/Tokyo`基準とし、同日ファイルがあれば新規作成せず更新する。
- 本日の目標、実施作業、主な変更ファイル、検証commandとPASS/FAIL/SKIP、決定事項、問題・risk、次作業を含める。
- 失敗・未完了作業も隠さず、原因と次の対応を残す。
- API key、token、認証header、個人情報、raw log全体を記録しない。
- 日次reportはGit追跡対象であり、現在の週次branchへ保存する。日次report専用commitは作らず、週次最終commitとPRへ含める。
- 週完了検知reviewの`reviews/` fileはローカル専用であるため、日次reportと分離する。

## 5. 共通Definition of Done

- 要求機能とエラー経路を実装済み。
- 新動作を検証するunit/integration testがある。
- 既存test、lint、type check、buildが成功。
- 外部API/LLMは標準testでmock/fixtureを利用。
- log、error、fixture、文書に秘密情報なし。
- `scripts/check-secrets.ps1`が成功し、禁止されたcredentialファイルがGit追跡対象ではない。
- 実行・設定・契約変更を関連文書へ反映。
- 仕様変更時は韓国語版と日本語版を同時更新。
- method単位コメントとTODO/FIXME説明は日本語。
- 開発した各日の日次reportが作成済み。
- 週次commit単体で対象週の結果をbuild/test可能。
- Pages対象変更はfixture artifact build、公開JSON Schema、Secret検査を通過する。

## 6. AI変更制限

- 依頼なしにAPI v1の既存field意味を変更しない。
- 国別独立処理とAPI/batch import境界を壊さない。
- test通過目的で検証を削除・弱化しない。
- unit testから実ニュースAPI/LLMを呼ばない。
- 利用者変更、運用data、reviewファイルを上書き・Git追加しない。
- 技術stackや主要構造変更にはADRと利用者確認が必要。
- 非保護HTTP、アプリ内秘密鍵、本文全体保存を許可しない。
- Web UIから静的JSONまたは`/api/v1`・`/api/v2` pathを分散直接参照せず、DataSource境界を使う。
- 実ニュース・LLM SecretはPR workflowで使わず、保護された運用workflowだけで使う。
- v2実装前に既存v1の`top_issues`意味を変更せず、producer・DataSource・Webを一緒に移行する。

## 7. LLM回帰検証

`sample-data/evaluation/{US,JP,KR}`に固定入力、`sample-data/evaluation/expected`に期待値を置く。文章完全一致ではなく、Schema、入力外ID/根拠禁止、国間混在禁止、決定的順位、上位3～5件の重複禁止、呼出量・費用上限を検査する。さらに国別100件以上の入力で一般語・媒体名・政治家名が上位結果に含まれず、複合名詞と関連記事接続が維持されることを確認する。実model評価は明示的なlive/evaluation作業だけで実行し、標準CIはmockを使う。

## 8. UI回帰検証

Web screenshot基準には、タイル、クラウド、loading、部分成功、cache復旧、小画面、文字拡大、長い多言語labelを含める。差分を自動承認せず、人が画像と意図を確認する。Android再開時は同じ状態のCompose基準を別途追加する。

## 9. Commitと復旧

全commit subjectは`YYYY/MM/DD <type>: <English> | <한국어> | <日本語>`形式を使い、3つのsummaryを同じ意味で記述する。週次branchでWIP commitを利用できるが、週完了検知reviewとCritical/High修正後にsquashまたはamendし、週次commit一つだけを残す。週次branchをpushしてDraft PRを一つ作成し、**Rebase and merge**で`main`へmergeする。候補commitをreview後に修正する場合は`--force-with-lease`だけを許可する。`Create a merge commit`は使わず、`Squash and merge`はローカル整理が不可能な例外時だけ許可する。merge後は最新`main`で全検証とsmoke testを実行し、失敗時は`codex/post-merge-fix-week-<number>` branchと別PRで修正する。完了後、状態文書へ週、PR番号、commit SHA、merge後検証結果を記録する。

## 10. 標準command

```powershell
.\scripts\check-spec-sync.ps1
.\scripts\check-secrets.ps1
.\scripts\verify-all.ps1
```

未作成projectの検査は`SKIP`表示とする。scaffoldが存在するのに必須tool/testを実行できない場合は失敗とする。
