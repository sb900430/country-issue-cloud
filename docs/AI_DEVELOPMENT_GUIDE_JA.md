# AI開発ガイド

本書は、AIと高速に開発しながらスコープ逸脱、検証漏れ、コンテキスト消失を防ぐための実行規則である。製品要件は`PROJECT_SPEC.md`と`PROJECT_SPEC_JA.md`に従う。

## 1. 固定技術選定

| 領域 | 選定 |
|---|---|
| Python環境・package | `uv`、`pyproject.toml`、lockfileをcommit |
| API | FastAPI、Pydantic v2系 |
| Android HTTP | Retrofit + Kotlinx Serialization |
| Android状態・保存 | ViewModel、Flow、Room、DataStore |
| Android DI | Hilt |
| Web | 静的HTML/CSS/Vanilla JS、npmベースの検査・テスト |
| 日時 | サーバーはUTC保存、`Asia/Tokyo`表示 |

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

## 目標commit
目標番号と最終commit message
```

不足項目は仕様と現コードから安全に判断できる範囲でAIが補完する。費用、外部契約、公開範囲、資格情報、復元困難な変更など利用者判断が必要な場合は実行前に質問する。

## 3. 作業手順

1. `AGENTS.md`、両仕様書、`docs/DEVELOPMENT_STATUS.md`を読む。
2. `main`を最新化し、対象目標の`codex/milestone-*` branchを作る。
3. `git status`で利用者変更を確認し保護する。
4. 要件、影響ファイル、検証基準を確認する。
5. 最小の完結単位で実装し、関連testを実行する。
6. 仕様へ影響する場合は韓国語・日本語版を同時更新する。
7. `scripts/verify-all.ps1`を実行し、開発状態文書を更新する。
8. WIPをsquashして目標commit一つに整理する。
9. 目標branchをpushし、`main`対象のDraft PRを作成する。
10. CIとreview通過後にReadyへ変更し、**Rebase and merge**でmergeする。
11. 最新`main`へ切り替え、`scripts/verify-all.ps1`と利用可能なローカルsmoke testを再実行する。
12. merge後検証が成功した場合だけ目標を完了扱いとし、次の目標branchを作る。

## 4. 共通Definition of Done

- 要求機能とエラー経路を実装済み。
- 新動作を検証するunit/integration testがある。
- 既存test、lint、type check、buildが成功。
- 外部API/LLMは標準testでmock/fixtureを利用。
- log、error、fixture、文書に秘密情報なし。
- 実行・設定・契約変更を関連文書へ反映。
- 仕様変更時は韓国語版と日本語版を同時更新。
- method単位コメントとTODO/FIXME説明は日本語。
- 目標commit単体でbuild/test可能。

## 5. AI変更制限

- 依頼なしにAPI v1の既存field意味を変更しない。
- 国別独立処理とAPI/batch import境界を壊さない。
- test通過目的で検証を削除・弱化しない。
- unit testから実ニュースAPI/LLMを呼ばない。
- 利用者変更、運用data、reviewファイルを上書き・Git追加しない。
- 技術stackや主要構造変更にはADRと利用者確認が必要。
- 非保護HTTP、アプリ内秘密鍵、本文全体保存を許可しない。

## 6. LLM回帰検証

`sample-data/evaluation/{US,JP,KR}`に固定入力、`sample-data/evaluation/expected`に期待値を置く。文章完全一致ではなく、Schema、入力外ID/根拠禁止、国間混在禁止、決定的順位、TOP 5重複禁止、呼出量・費用上限を検査する。実model評価は明示的なlive/evaluation作業だけで実行し、標準CIはmockを使う。

## 7. UI回帰検証

Compose screenshot基準には、タイル、クラウド、loading、部分成功、offline、小画面、文字拡大、長い多言語labelを含める。差分を自動承認せず、人が画像と意図を確認する。

## 8. Commitと復旧

全commit subjectは`YYYY/MM/DD <type>: <English> | <한국어> | <日本語>`形式を使う。日付は実際のcommit日、typeは英語とし、3つのsummaryは同じ意味を簡潔に翻訳する。例は`2026/08/03 feat: scaffold local environment | 로컬 환경 구성 | ローカル環境を構成`である。目標別branchのWIPにも同形式を適用し、完了時にsquashして目標commit一つへ整理する。Critical/Highの事後修正は別`codex/review-fix-*` branchと`fix:` commitで処理する。目標とreview修正はすべてDraft PRを通して**Rebase and merge**で`main`へmergeし、直接pushしない。`Create a merge commit`は使わない。ローカルでWIPをsquashできなかった例外時だけ`Squash and merge`を許可し、squash commit subjectを所定の日付・3言語形式で手動入力する。merge後は最新`main`で全検証とsmoke testを再実行し、merge conflict、依存関係組合せ、統合errorがないことを確認する。失敗時は`codex/post-merge-fix-<milestone>` branchで修正し、別PRを作る。完了後、状態文書へPR番号、SHA、merge後検証結果を記録する。

## 9. 標準command

```powershell
.\scripts\check-spec-sync.ps1
.\scripts\verify-all.ps1
```

未作成projectの検査は`SKIP`表示とする。scaffoldが存在するのに必須tool/testを実行できない場合は失敗とする。
