# 国別イシュークラウド（Country Issue Cloud）

> 米国・日本・韓国の経済ニュースを国別に独立して分析し、各国でその日に注目された経済イシューを意味ベースのクラウドとして表示するAndroidアプリケーション

## 文書情報

| 項目 | 内容 |
|---|---|
| 目的 | 企画・設計・開発・テスト・配布・運用の単一基準 |
| プロジェクト名 | 国別イシュークラウド |
| 英語名 | Country Issue Cloud |
| アプリ名 | イシュークラウド |
| リポジトリ名 | `country-issue-cloud` |
| 基準タイムゾーン | `Asia/Tokyo` |

重要な設計変更は本書とコードへ同時に反映し、`docs/adr/`にADRとして残す。韓国語版は`PROJECT_SPEC.md`であり、両ファイルは同一仕様を記述する対等な基準文書である。関連内容を変更する場合は、韓国語版と日本語版を同じ作業・同じコミットで更新する。

---

## 1. プロジェクト概要

毎日、米国・日本・韓国の経済ニュースを国別に独立収集する。各国内で意味の近い記事や表現を一つのイシューにまとめ、ユニーク記事数と媒体の多様性を基準に国別TOP 5を計算する。利用者は同じ日付に各国が何を重要視したかを国タブで切り替えて確認する。

本プロジェクトは、次を目的とする非商用ポートフォリオである。

1. 実際に動作するAndroidアプリを制作し、Google Playで配布する。
2. 設計・開発・テスト・配布の履歴をGitHubで公開する。
3. データが毎日更新されるサービスを実運用する。
4. 多言語処理、LLM構造化出力、バッチ/API分離、オフライン、CI/CDの能力を示す。

### 利用者価値

- 同じ日付の3か国の経済的関心を素早く比較できる。
- 単語頻度ではなく、類似表現を意味単位にまとめたイシューを確認できる。
- 記事数、媒体数、代表出典から選定根拠を確認できる。
- オフラインでも最後に正常取得した結果を確認できる。

### 対象外

- 3か国共通キーワードの積集合は計算しない。
- 一国のキーワードを3言語へ翻訳し、共通結果として表示しない。
- LLMに最終順位を任意決定させない。
- 記事本文全体を保存・再配布しない。
- 非公式HTMLスクレイピングを使用しない。
- 投資推奨や金融助言を提供しない。

---

## 2. 成功基準とスコープ

### 成功基準

- AndroidアプリをGoogle Playの本番、または公開可能なテストトラックへ登録する。
- 最低2か国の結果を毎日自動更新する。
- 直近7日間の国別TOP 5と根拠記事を確認できる。
- オフラインで最後の正常データを表示できる。
- Webデモと運用APIへ外部からアクセスできる。

| 指標 | 目標 |
|---|---:|
| 直近30日のバッチ公開成功率 | 95%以上 |
| API可用性の内部目標 | 99%以上 |
| キャッシュヒット時のAPI応答時間 | 500ms以内 |
| 最終正常データ | 48時間以内 |
| 国別の正常推奨サンプル | 30件以上 |
| 国別の公開可能サンプル | 15件以上 |
| イシュー抽出成功率 | 80%以上 |

### 初回リリースに含むもの

- 国別収集、整形、重複排除、イシュークラスタリング、TOP 5
- 直近7日分のJSON保存とFastAPI
- Androidのタイル/クラウド、詳細、Roomキャッシュ
- 部分成功、遅延、メンテナンス、エラー状態
- 静的Webデモ
- 自動レビューとMarkdown障害レポート
- VPS、HTTPS、systemd、GitHub Actions
- Google Playテストとリリース準備

### 初回リリースの対象外

- ログイン、コメント、広告、決済、パーソナライズ推薦
- サーバー同期型お気に入り、プッシュ通知
- iOS、7日を超える履歴、リアルタイムストリーミング

---

## 3. 基本原則

```text
米国の経済ニュース全体 → 米国イシューTOP 5
日本の経済ニュース全体 → 日本イシューTOP 5
韓国の経済ニュース全体 → 韓国イシューTOP 5
```

- 共通テーマを先に決めて3か国で検索しない。
- 一国の失敗が他国の処理・表示を妨げない。
- イシュー名は原語を基準とし、米国・日本には韓国語補助名を付けられる。
- 補助翻訳は集計・順位に使わない。
- 記事にない表現を根拠として生成しない。
- LLMは抽出とクラスタリングのみを担当する。
- 順位はユニーク記事数、ユニーク媒体数、最新時刻、`issue_id`の順でコードが計算する。
- 公式APIまたは公開RSSのみを使用し、本文全体と画像を保存しない。
- APIとバッチは相互の実行モジュールをimportせず、公開JSONだけで通信する。
- 一時ファイル作成、Schema検証、アトミック置換の順で結果を公開する。

---

## 4. 機能要件

| ID | 機能 | 説明 |
|---|---|---|
| F-01 | 国別収集 | 国別に最大100件の経済ニュースを独立収集 |
| F-02 | 整形・重複排除 | URL、タイトル、類似度で国内重複を排除 |
| F-03 | イシュー抽出 | LLMで経済イシュー候補を抽出 |
| F-04 | クラスタリング | 国内の類似表現と記事を統合 |
| F-05 | TOP 5 | 記事数と媒体数で順位算出 |
| F-06 | 結果保存 | 日付JSONとlatestをアトミック保存 |
| F-07 | 品質レビュー | サンプル、偏り、抽出率、ラベルを点検 |
| F-08 | 障害レポート | 原因、影響、改善案、スタックを記録 |
| F-09 | 保管 | 結果7日、レポート90日、ログ30日 |
| F-10 | 定期実行 | systemd timerと制限付き再試行 |
| F-11 | 日付照会 | 直近7日間の利用可能日を提供 |
| F-12 | 国切替 | 同一日付の国別結果を即時切替 |
| F-13 | イシュー可視化 | TOP 5を基本タイル型またはクラウド型で切替表示 |
| F-14 | 詳細 | 統計、代表記事、原文リンク |
| F-15 | オフライン | Roomキャッシュで直近結果を表示 |
| F-16 | アプリ設定 | メンテナンス、バージョン、告知、ポリシーURL |
| F-17 | 状態 | 最新データと国別状態を提供 |

---

## 5. 収集ポリシー

- サービスタイムゾーン：`Asia/Tokyo`
- バッチ：毎日08:00
- 収集範囲：実行時刻から直前24時間
- 内部時刻：UTC、表示：タイムゾーン付きISO 8601
- 公開時刻がない記事、または現在より10分以上未来の記事は除外する。

| 区分 | 基準 |
|---|---:|
| 国別目標 | 最大100件 |
| 正常推奨数 | 30件以上 |
| 公開最小数 | 15件以上 |
| 単一媒体の最大反映 | 20件推奨 |
| 媒体偏重警告 | 40%超 |
| 重大な偏重 | 60%超 |

100件への到達より適法性と透明性を優先し、実際の記事数をアプリに表示する。

### 出典ポリシー

- NewsAPI無料プランはローカル開発・テストにのみ使う。
- 運用では公式RSSまたは運用利用が許可された公開APIのみ使う。
- 国別に最低2つの出典を目標とする。
- 日本の公式ソースとNAVER API HUBの運用条件確認をリリースゲートとする。
- ソースごとの利用条件確認日と許可フィールドを設定へ記録する。

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

### 重複排除

1. トラッキングパラメータを除去したURLの一致
2. HTML・空白・句読点・大小文字を正規化したタイトルの一致
3. タイトル類似度0.92以上、公開時刻差6時間以内

代表記事は、タイトル・要約の存在、有効時刻、HTTPSリンク、早い公開時刻の順で選ぶ。

---

## 6. LLMと集計

LLMは翻訳ワードクラウドを作るためではなく、一国内の類似した出来事を意味単位でまとめるために使う。

```text
基準金利据え置き / 金融通貨委員会の金利決定 / 韓国銀行の金融政策
→ 基準金利据え置き
```

LLMはイシュー候補、国内クラスタ、原語ラベル、韓国語補助名、構造化JSONを生成する。国をまたぐ統合、順位決定、投資判断は行わない。

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

- JSON Schema/Pydantic検証
- 入力に存在する記事IDと根拠表現のみ許可
- モデル/プロンプトバージョンを記録し、可能ならtemperature 0
- 記事10～20件単位の処理と内容ハッシュキャッシュ
- timeout 30秒、最大2回再試行
- 月額USD 10上限、USD 5相当で警告

```text
article_count   = イシューのユニーク記事数
publisher_count = イシューのユニーク媒体数
article_ratio   = イシュー記事数 / 国の有効記事数
```

`success`：記事30件以上、LLM成功率80%以上、イシュー3件以上。

`partial_success`：記事15件以上、LLM成功率70%以上、イシュー1件以上。

最低2か国が公開可能な場合に日付結果を保存し、失敗実行では`latest.json`を変更しない。

---

## 7. データSchemaと保管

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

| データ | 保管期間 |
|---|---:|
| 日付別結果 | 当日を含む7日 |
| `latest.json` | 最新1件 |
| 成功時の一時データ | バッチ後直ちに削除 |
| 失敗時の一時データ | 24時間 |
| 障害レポート/実行要約 | 90日 |
| アプリケーションログ | 30日 |

---

## 8. API設計

基本パスは`/api/v1`とする。

| Method | Path | 説明 |
|---|---|---|
| GET | `/issues/latest` | 最終公開結果 |
| GET | `/issues/dates` | 直近7日の利用可能日 |
| GET | `/issues/{date}` | 1日分の3か国結果 |
| GET | `/issues/{date}/{country}` | 指定日・指定国の結果 |
| GET | `/status` | データ鮮度と国別状態 |
| GET | `/app-config` | メンテナンス、バージョン、告知、ポリシーURL |
| GET | `/health` | プロセス生存確認 |
| GET | `/ready` | ストレージを含む準備状態 |

| HTTP | エラーコード | 条件 |
|---:|---|---|
| 400 | `invalid_date` | 日付形式エラー |
| 400 | `date_out_of_range` | 直近7日の範囲外 |
| 400 | `invalid_country` | US/JP/KR以外 |
| 404 | `issue_not_found` | 日付結果なし |
| 404 | `country_not_available` | 国別結果なし |
| 503 | `service_maintenance` | メンテナンス中 |
| 500 | `internal_error` | サーバー内部エラー |

- エラー応答には`request_id`だけを提供し、内部詳細を隠す。
- `ETag`、`Last-Modified`、`Cache-Control`をサポートする。
- リリース済みv1フィールドの削除や意味変更をしない。
- アプリへニュースAPI・LLMの秘密鍵を含めない。
- nginx rate limitを適用する。

---

## 9. Androidアプリ設計

| 区分 | 選定 |
|---|---|
| 言語/UI | Kotlin、Jetpack Compose、Material 3 |
| 構造 | UI → ViewModel → Repository → Room/API |
| ネットワーク | Retrofit |
| JSON | Kotlinx Serialization |
| 保存 | Room、DataStore |
| 非同期/DI | Coroutines、Flow、Hilt |
| 最小SDK | API 26 |
| Target SDK | リリース時のPlay要件を満たす。初期目標API 36 |
| 配布 | AAB、Play App Signing |

### コードコメントの言語

- メソッド・関数単位の説明コメント、KDoc、docstringは日本語だけで記述する。
- 目的、引数、戻り値、例外、重要な前提条件の説明が必要な場合は日本語を使う。
- 自明なコードへ無理にコメントを追加せず、実装と命名で意図を表す。
- TODO/FIXMEの説明文も日本語で記述する。ライブラリ名、API名、コード識別子、公式エラーメッセージは原文を維持できる。
- Kotlin、Python、JavaScript、および今後追加される全ソースコードへ同じ規則を適用する。

### 画面

1. 初期ローディング
2. イシュークラウドホーム
3. イシュー詳細と代表記事
4. プロジェクト情報
5. プライバシーポリシー/問い合わせ
6. オープンソースライセンス
7. メンテナンス/更新案内

ホーム画面は、アプリ名/基準日、国タブ、直近7日、`今日のイシューTOP 5`可視化、最終更新時刻、更新ボタンの順とする。国タブは同一日付の応答を利用し、追加リクエストなしで切り替える。日付変更時のみリクエストする。

### ホーム画面UI確定案

TOP 5は一つの可視化領域だけで提供し、同じ5件を下部リストへ重複表示しない。

| 項目 | 確定動作 |
|---|---|
| 基本表示 | 加重タイル型（C案） |
| 代替表示 | 自由配置イシュークラウド（A案） |
| 切替方法 | 可視化領域右上の`タイル / クラウド`スライド型セグメントボタン |
| 状態保存 | 初回はタイル型。以後は最後の選択をDataStoreへ保存し、再起動時に復元 |
| 共通タイトル | `今日のイシューTOP 5` |
| 共通情報 | 分析記事数とデータ生成/更新時刻 |
| 下部領域 | 最終更新時刻と更新ボタンのみ |
| 詳細遷移 | タイルまたはクラウドのキーワードから同一の詳細画面へ遷移 |

タイル型は順位、イシュー名、記事数を各タイルに表示する。1位を最大とし、残りは重要度でサイズと明度を変える。タイル全体をタッチ領域とする。

クラウド型は同じTOP 5を横書きで配置し、`article_ratio`で文字サイズと明度を変える。回転・重なりを避け、キーワードから関連記事を開ける案内を表示する。順位と正確な記事数はアクセシビリティ説明と詳細画面で確認できるようにする。

表示切替ではデータ再取得・再集計を行わず、同一ViewModel状態を別Composeコンポーネントで描画する。国・日付・ロード・エラー状態とスクロール位置を維持する。

```text
IssueHomeScreen
├── CountryTabs
├── RecentDateSelector
├── IssueSectionHeader
│   ├── ArticleSummary
│   └── IssueViewModeToggle
├── IssueVisualization
│   ├── WeightedIssueTiles
│   └── DeterministicIssueCloud
└── UpdateFooter
    ├── LastUpdatedText
    └── RefreshButton
```

### クラウドルール

- 国別`article_ratio`で文字サイズを計算する。
- 最小/最大サイズを制限し、順位ベースの決定的配置を使う。
- ランダム回転、過剰な色、色だけによる区別を避ける。
- アクセントカラー一色と明度差だけを使う。
- 長いラベルは最大2行とし、選択時に詳細へ移動する。

### 状態

| 状態 | 処理 |
|---|---|
| 正常 | 選択された方式でTOP 5を表示 |
| ローディング | スケルトンと入力制限 |
| 本日分未準備 | 最新日へフォールバックし案内 |
| 部分成功 | 該当国へ制限案内 |
| 国別失敗 | 該当国だけ更新遅延を表示 |
| オフライン+キャッシュ | キャッシュと最終確認時刻 |
| オフライン+キャッシュなし | 接続案内と再試行 |
| サーバーエラー | 既存キャッシュを維持 |
| メンテナンス | サーバー提供文言 |
| 古いアプリ | 任意/必須アップデート案内 |

Roomを読み取り基準データとし、有効なサーバー応答だけを保存する。直近7日だけを保持し、選択国・日付をプロセス再生成後も復元する。TalkBack、文字拡大、最小タッチ領域、コントラスト、タブレット/フォルダブル、多言語グリフを検証する。

---

## 10. バックエンドとプロジェクト構成

```text
country-issue-cloud/
├── backend/app/
│   ├── main.py
│   ├── core/
│   ├── api/v1/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   └── batch/
├── backend/tests/
├── android/
├── frontend/
├── config/
├── deploy/
├── docs/
│   ├── AI_DEVELOPMENT_GUIDE.md
│   ├── AI_DEVELOPMENT_GUIDE_JA.md
│   ├── DEVELOPMENT_STATUS.md
│   ├── DEVELOPMENT_STATUS_JA.md
│   └── adr/
├── sample-data/
├── scripts/
│   ├── check-spec-sync.ps1
│   └── verify-all.ps1
├── .github/workflows/
├── PROJECT_SPEC.md
├── PROJECT_SPEC_JA.md
├── README.md
└── .env.example
```

Repository最小契約：

```python
find_by_date(date)
find_latest()
find_available_dates(within_days)
save(result)
delete_expired(retention_days)
```

JSONをSQLite/PostgreSQLへ変更してもRouter、Service、Android API契約を維持する。Webデモは静的HTML/CSS/Vanilla JSで作り、Androidと同じAPI・状態定義を使う。最大幅720px、アクセントカラー一色、簡潔なクラウドデザインを適用する。

---

## 11. バッチとスケジューリング

```text
1. OS lock取得
2. 設定とソース確認
3. US/JP/KR並列収集
4. 国別整形・重複排除
5. 国別LLMイシュー抽出
6. 国別クラスタリング
7. 国別TOP 5集計
8. 品質レビュー
9. 公開条件判定
10. 一時JSON作成・検証
11. 日付ファイルをアトミック置換
12. latest.json更新
13. 期限切れデータ削除
14. 実行要約とlock解除
```

| 時刻 | 処理 |
|---|---|
| 08:00 | 基本バッチ |
| 08:30 | 結果がない場合の1回目再試行 |
| 09:30 | 最終再試行 |
| 10:00 | 状態確認と連続失敗通知候補 |

systemd timerに`Persistent=true`を使う。公開済み日付は原則スキップし、OSファイルロックで同時実行を防ぐ。

```text
python -m app.batch.pipeline_entry
python -m app.batch.pipeline_entry --date 2026-07-29
python -m app.batch.pipeline_entry --dry-run
python -m app.batch.pipeline_entry --force
python -m app.batch.pipeline_entry --countries US,JP
```

`--dry-run`は公開ファイルを変更しない。`--force`は新結果の検証成功時のみ置換する。lock取得失敗は`skipped_locked`として記録する。障害レポートには実行ID、失敗国/段階、例外、原因分類、影響、再試行、改善案3件、マスキング済みスタックを記録する。一国の失敗と期限切れ削除失敗は、可能なら全体を中断させない。

---

## 12. セキュリティ・プライバシー・Google Play

### アプリとサーバー

- ログイン、広告、位置情報・連絡先・写真・ストレージ権限を使用しない。
- Androidは`INTERNET`権限のみ使う。
- HTTPSを強制し、秘密鍵はサーバー環境変数だけに保存する。
- 日付/国入力を検証し、ユーザー入力からファイルパスを作らない。
- 非rootアカウント、最小ファイル権限、nginx rate limitを使う。
- ログとレポートでAPIキーと認証ヘッダーをマスキングする。

### プライバシーポリシー

データを直接収集しない場合でもData SafetyフォームとポリシーURLを提供する。

- 開発者/運営主体と問い合わせ先
- アプリ/サーバーが処理する情報とアクセスログ
- 外部サービスとSDK
- 処理目的、保管期間、削除ポリシー
- 第三者提供の有無
- 施行日と変更履歴

### Google Play

- デベロッパーアカウント、本人確認、登録料予算
- AABとPlay App Signing
- リリース時にTarget API要件を再確認
- 新規個人アカウントの非公開テスト要件を満たす
- Data Safety、プライバシーポリシー、コンテンツレーティング
- ニュース・雑誌アプリ申告対象として準備
- アプリ内に運営者連絡先、記事出典、公開日を表示
- アイコン、フィーチャーグラフィック、スクリーンショット、説明文を準備
- 自動分析結果であり投資助言ではないことを告知

```text
アプリ名：イシュークラウド
サブタイトル：米国・日本・韓国の今日の経済イシュー
短い説明：3か国が今日注目した経済イシューを国別に確認できます。
```

---

## 13. テスト戦略

### バックエンド・バッチ

- URL/タイトル重複排除と安定した同順位ソート
- 日付範囲、タイムゾーン、アトミック保存、期限切れ削除
- 3か国正常フローと一国失敗後の継続処理
- 2か国部分成功公開、1か国成功時のlatest非更新
- LLM形式エラー、再試行、根拠検証
- 障害レポート、秘密情報マスキング、重複lock
- 外部API/LLMはmockとfixtureを利用

### API

- latest/dates/日付/国の正常応答
- 範囲外400、データなし404、メンテナンス503
- ETag 304と破損ファイル処理
- 入力によるパストラバーサル防止

### Android

- 国切替時に追加リクエストなし、日付切替時にリクエストあり
- 初回はタイル型、最後の表示選択を再起動後に復元
- タイル/クラウド切替で再取得・再集計なし
- 両表示から同じイシュー詳細へ遷移
- TOP 5の重複下部リストを描画しない
- 本日分未準備のフォールバック案内を維持
- 古い非同期応答が最新UIを上書きしない
- オフラインキャッシュと破損応答防御
- 画面/プロセス再生成後の状態復元
- TalkBack、文字拡大、長い多言語ラベル
- 小画面、タブレット、フォルダブル
- release AABから運用APIへ接続
- タイル型・クラウド型・各状態のCompose screenshot回帰test

### LLM回帰評価

- `sample-data/evaluation/{US,JP,KR}`に国別固定入力を置く。
- `sample-data/evaluation/expected`には文章全体ではなく、Schema、根拠ID、重複禁止、決定的順位の期待値を置く。
- 標準CIはmockのみを使い、実model評価は明示的なlive/evaluation実行へ分離する。
- promptまたはclustering変更時に国間混在、入力外根拠、TOP 5重複、費用上限を再検証する。

### Web

- 国のローカル切替と日付API呼出
- 無効日付のクリック防止
- ロード/部分成功/エラー状態
- モバイル日付行の横スクロール

### 週次自動レビュー

- 実行：2026年8月8日から9月26日まで毎週土曜日10:00（JST）
- 範囲：前回レビュー以降のcommit/diff、関連テスト・ビルド・静的検査
- 評価：セキュリティ、正確性、性能、保守性、テスト十分性、文書・アーキテクチャ準拠
- 結果：ローカル専用`reviews/YYYY-MM-DD-weekly-review.md`

| 重大度 | 対応 |
|---|---|
| Critical | 安全に即時修正・再検証し、`RESOLVED`と根拠を残す。修正不能なら`UNRESOLVED/BLOCKED`。 |
| High | Criticalと同様に修正・再検証して状態を記録。 |
| Medium | 自動修正せず、ファイル・行・影響・推奨対応を履歴化。 |
| Low | 自動修正せず、改善候補として履歴化。 |

`reviews/`は`.gitignore`へ含め、レビューMDはローカルだけに保存する。Critical/High修正は検証通過時に修正コードだけを明確なコミットにし、`origin/main`へpushする。ローカルレビューへ`RESOLVED`と修正コミットSHAを記録する。Critical/Highがなければcommit/pushしない。外部契約、資格情報、利用者判断が必要な項目を勝手に回避しない。

---

## 14. 配布と運用

```text
Internet
  → nginx (80/443, TLS)
      → /       静的Web
      → /api/   FastAPI/uvicorn

systemd
  → issue-cloud-api.service
  → issue-cloud-batch.service
  → issue-cloud-batch.timer
```

- 初回設定と反復配布を分離する。
- 配布後に`/health`、`/ready`を検証する。
- 失敗時は直前の正常リリースへロールバックする。
- サーバーに直近2リリースを保持する。

運用指標は、バッチ時間、国・ソース別記事数/失敗率、LLM呼出・token・費用・再試行・成功率、最終公開成功時刻、API要求数・エラー率・応答時間とする。24時間遅延で案内、48時間遅延でアプリ警告を表示する。運用Runbookにソース認証/形式変更、LLM費用急増、JSON復旧、サービス再起動、証明書障害、ロールバックを含める。

---

## 15. GitHubとCI/CD

Git除外対象：

```text
.env
*.jks
*.keystore
key.properties
google-services.json
local.properties
data/
reports/
reviews/
*.log
```

READMEにはアプリ/Webリンク、スクリーンショット、アーキテクチャ、技術選定、実行方法、API例、テスト、出典・LLM・運用ポリシーを含める。MIT License、secret scanning、依存関係更新、Issue/PRテンプレートを使う。

Pull Request CI：

- 共通：韓国語・日本語仕様の同時変更と主要構造の同期検査
- Python：Ruff、mypy、pytest、import境界、セキュリティ検査
- Android：ktlint、detekt、Android Lint、テスト、debugビルド
- Web：静的検査、JSテスト、基本アクセシビリティ検査

```text
main merge → 全CI → VPS配布 → health/ready → 失敗時ロールバック
v* tag → release AAB → GitHub Release → Play内部テストトラック
```

### AI開発ガードレール

- 実装作業は目標、範囲、対象外、完了条件、検証command、目標commitを含む作業契約に従う。
- `docs/AI_DEVELOPMENT_GUIDE.md`と日本語版をAI作業の実行基準とする。
- `docs/DEVELOPMENT_STATUS.md`と日本語版へ現在目標、完了commit、検証結果、次作業、外部依存を記録する。
- 共通完了条件に機能・エラー経路、関連test、lint/type/build、秘密情報検査、文書同期、日本語コメント規則を含める。
- 目標commit前に`scripts/verify-all.ps1`を実行し、仕様同期と各project検査を一つの入口で行う。
- 目標branchの一時WIP commitは許可するが、完了時にsquashして目標単位commit一つへ整理する。
- AIがAPI契約、主要architecture、技術stack、費用・公開範囲を変える場合はADRと利用者確認が必要。
- UI screenshot基準変更は自動承認せず、人が意図された変更か確認する。

---

## 16. コスト計画

| 項目 | ポリシー |
|---|---|
| Google Play | 1回限りの登録料を計上 |
| VPS/ドメイン | 低価格の月額固定費を事前確定 |
| NewsAPI | 運用利用せず、ローカル開発のみ |
| 運用ニュースソース | 無料・利用可能なソース優先 |
| LLM | 月額USD 10上限 |
| HTTPS | 無料証明書 |
| GitHub Actions | 無料枠内を目標 |

外部サービス料金と規約は本番配布直前に再確認する。

---

## 17. 開発スケジュール

2026年8月3日月曜日に開始する、AI開発支援前提のローカル優先日程である。ホスティング契約前はfixture、ローカルFastAPI、Android Emulatorを使い、4週間でローカルMVPを完成する。既存8目標は削らず、2目標ずつ連続・並行実施する。月～金曜日に開発し、土曜日10:00（JST）に自動レビューする。日曜日は休息・遅延吸収日とし、固定作業を置かない。

### 週別目標

| 週 | 期間 | 対象目標 | 完了基準 |
|---|---|---|---|
| 1週目 | 8/3～8/8 | 1 環境・骨格、2 データ・API、3 収集・整形 | ローカルAPIと3か国収集基盤が動作 |
| 2週目 | 8/10～8/15 | 4 LLM・TOP 5、5 バッチ・Web | 国別TOP 5をバッチ→API→Webで実演 |
| 3週目 | 8/17～8/22 | 6 Android接続、7 確定UI・オフライン | Emulatorで確定UIとオフライン照会を検証 |
| 4週目 | 8/24～8/29 | 8 安定化・ポートフォリオ | 全体フロー再現と`v0.8.0-local-mvp`候補 |

### 1週目 — 基盤、ローカルAPI、国別収集

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/3(月) | 環境、monorepo、設定分離、fixture、CI、AI開発検証入口 | 目標1検証・`feat: scaffold local development environment` |
| 8/4(火) | データモデル、Schema、JSON Repository | fixture・Repositoryテスト |
| 8/5(水) | アトミック保存、保管、FastAPI | 目標2検証・`feat: implement local data API` |
| 8/6(木) | Collector、fixture/実ソース、重複排除 | 契約・重複排除テスト |
| 8/7(金) | 国別並列収集、失敗隔離、データモード | 目標3検証・`feat: implement country news collection` |
| 8/8(土) | 自動レビュー | ローカルレビュー、Critical/High修正 |

### 2週目 — LLM、全体バッチ、Webデモ

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/10(月) | LLM interface、mock、構造化出力、実adapter | mockと限定実呼出検証 |
| 8/11(火) | 国内cluster、根拠検証、決定的TOP 5 | 統合・幻覚防止・同順位テスト |
| 8/12(水) | cache、timeout/retry、token/費用 | 目標4検証・`feat: implement issue extraction and ranking` |
| 8/13(木) | pipeline、部分成功、lock、retry、report | 失敗・重複実行・maskテスト |
| 8/14(金) | 静的Webと状態処理、統合実行 | 目標5検証・`feat: complete batch pipeline and web demo` |
| 8/15(土) | 自動レビュー | ローカルレビューと重大度別履歴 |

### 3週目 — Android接続、確定UI、オフライン

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/17(月) | Compose、Material 3、Hilt、Navigation、Repository | 基本構造とmockテスト |
| 8/18(火) | Emulator API接続、国・日付選択、基本状態 | 目標6検証・`feat: connect android app to local API` |
| 8/19(水) | C案タイル型、重複リストなしホーム | 順位・記事数・詳細選択 |
| 8/20(木) | A案クラウド、切替、DataStore | 無通信切替・再起動復元テスト |
| 8/21(金) | 詳細、Room、オフライン・エラー状態 | 目標7検証・`feat: implement android issue UI and offline cache` |
| 8/22(土) | 自動レビュー | ローカルレビューと重大度別履歴 |

### 4週目 — ローカルMVP安定化とポートフォリオ

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/24(月) | 全体回帰テストと不具合修正 | 全テスト通過記録 |
| 8/25(火) | 性能、cache、復旧、アクセシビリティ、多端末 | 性能・互換性結果 |
| 8/26(水) | ワンクリック実行と新環境再現 | 文書だけで全体実行 |
| 8/27(木) | README、architecture、画像、demo | GitHubポートフォリオ完成 |
| 8/28(金) | release URL、secret検査、最終実演 | 目標8検証・`release: complete local MVP` |
| 8/29(土) | 自動レビュー | 最終ローカルレビュー |

### 目標単位コミットポリシー

| 目標 | コミットメッセージ |
|---|---|
| 1 環境・骨格 | `feat: scaffold local development environment` |
| 2 データ・API | `feat: implement local data API` |
| 3 国別収集・整形 | `feat: implement country news collection` |
| 4 LLM・TOP 5 | `feat: implement issue extraction and ranking` |
| 5 バッチ・Web | `feat: complete batch pipeline and web demo` |
| 6 Android API接続 | `feat: connect android app to local API` |
| 7 Android UI・オフライン | `feat: implement android issue UI and offline cache` |
| 8 MVP安定化 | `release: complete local MVP` |

各目標は実装と関連テストの通過後に1回コミットする。作業中の一時コミットは完了前にsquashする。各目標コミットは単独でビルド・テスト可能とする。レビュー前の未コミットCritical/High修正は目標コミットへ含める。push済み目標で見つかったCritical/Highだけは別`fix:`コミットを許可し、ローカルレビューへSHAを残す。

### ホスティング契約後1週目 — 運用配布

| 営業日 | 内容 | 完了基準 |
|---|---|---|
| 1日目 | VPS、ドメイン、非root、firewall | 基本セキュリティ確認 |
| 2日目 | nginx、TLS、FastAPI systemd | HTTPS APIアクセス |
| 3日目 | バッチservice/timer、運用環境変数 | 手動・予約バッチ成功 |
| 4日目 | GitHub Actions、health/ready、rollback | 配布・検証・rollback訓練 |
| 5日目 | Android release URLとAAB smoke test | ロジック変更なしで運用API接続 |
| 以後7日 | 自動バッチ、費用、エラー、品質観察 | 7日連続運用記録 |

### ホスティング契約後2週目以降 — Playテストとリリース

| 段階 | 内容 | 完了基準 |
|---|---|---|
| 1～2日目 | プライバシー、Data Safety、ニュース申告 | Play提出文書完成 |
| 3日目 | 署名AAB、ストア画像・説明 | 内部テストupload |
| 4～5日目 | 内部テスト、実機smoke、修正 | 主要フロー通過 |
| ポリシー要求期間 | 非公開テストとfeedback反映 | 人数・期間要件充足 |
| リリース日 | `v1.0.0`、GitHub Release、段階配布 | Play・Demo・GitHub公開 |

| リリース後周期 | 作業 |
|---|---|
| 毎日 | バッチと最新データ自動確認 |
| 毎週 | 障害、費用、媒体偏重レビュー |
| 毎月 | 依存関係、復旧テスト、費用レビュー |
| 90日ごと | ニュースソース規約再確認 |
| ポリシー変更時 | Target SDK、Data Safety、SDKポリシー確認 |

---

## 18. バージョン計画

```text
v0.1.0 設計とscaffold
v0.2.0 RepositoryとFastAPI
v0.3.0 ニュース収集と整形
v0.4.0 LLMイシュー抽出と集計
v0.5.0 バッチレビューと障害レポート
v0.6.0 Webデモ
v0.7.0 Android主要UI
v0.8.0 オフラインと安定化
v0.9.0 VPSとPlay非公開テスト
v1.0.0 初回公開リリース
```

---

## 19. リリースゲート

- [ ] 収集が特定テーマ検索へ偏っていない
- [ ] 最低2か国の運用ソース利用条件確認
- [ ] 7日連続自動バッチ結果
- [ ] 一国失敗時に他国結果を維持
- [ ] LLM結果に存在しない記事/表現なし
- [ ] API 200/400/404/503検証
- [ ] Androidオフライン・キャッシュ復旧検証
- [ ] release AABが運用APIで動作
- [ ] プライバシー、問い合わせ、出典、公開日表示
- [ ] GitHubに秘密鍵・運用データなし
- [ ] VPS rollback検証
- [ ] Play申告・テスト要件充足
- [ ] READMEでアプリ/Web/設計/テストを確認可能

---

## 20. 主なリスク

| リスク | 対応 |
|---|---|
| 無料ソース不足/規約変更 | 複数adapter、設定化、実サンプル公開 |
| 検索語偏重 | カテゴリ/RSS全体収集、query記録 |
| LLM誤分類 | ID/根拠検証、sample review、version管理 |
| LLM費用増 | batch、cache、月額USD 10上限 |
| 国別収集失敗 | 独立処理、部分成功、遅延案内 |
| JSON破損 | 一時作成、検証、atomic置換 |
| VPS障害 | health monitor、systemd、cache、rollback |
| Play審査遅延 | ポリシー資料の先行準備とbuffer |
| 公開リポジトリ鍵漏洩 | `.gitignore`、secret scan、鍵rotation |

---

## 21. 最終成果物

- [ ] 統合仕様、画面/機能/アーキテクチャ設計とADR
- [ ] データ・出典ポリシーとAPI仕様
- [ ] PythonバッチとFastAPI
- [ ] AndroidアプリとWebデモ
- [ ] 自動テストとCI/CD
- [ ] 配布script、nginx、systemd
- [ ] 運用Runbookと障害レポート例
- [ ] プライバシーポリシーと問い合わせページ
- [ ] Google Play登録資料
- [ ] README、デモ画像、GitHub Release

---

## 22. 最終定義

> 国別イシュークラウドは、米国・日本・韓国の経済ニュースを国別に独立収集し、LLMで各国内の類似した記事表現をイシュー単位へまとめ、ユニーク記事数と媒体多様性に基づく国別TOP 5をタイルまたはクラウドで表示するAndroid/Webアプリケーションである。結果には実際の出典とサンプル数を提示し、バッチ失敗、オフライン、外部API費用などの運用課題を明示的に処理する。
