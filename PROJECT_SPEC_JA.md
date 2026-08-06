# 国別イシュークラウド（Country Issue Cloud）

> 米国・日本・韓国の経済ニュースを国別に独立分析し、各国でその日に注目された経済イシューをURLで確認するレスポンシブWebアプリケーション

## 文書情報

| 項目 | 内容 |
|---|---|
| 目的 | 企画・設計・開発・テスト・配布・運用の単一基準 |
| プロジェクト名 | 国別イシュークラウド |
| 英語名 | Country Issue Cloud |
| サービス名 | イシュークラウド |
| リポジトリ名 | `country-issue-cloud` |
| 基準タイムゾーン | `Asia/Tokyo` |

重要な設計変更は本書とコードへ同時に反映し、`docs/adr/`にADRとして残す。韓国語版は`PROJECT_SPEC.md`であり、両ファイルは同一仕様を記述する対等な基準文書である。関連内容を変更する場合は、韓国語版と日本語版を同じ作業・同じコミットで更新する。

---

## 1. プロジェクト概要

毎日、米国・日本・韓国の経済ニュースを国別に独立収集する。各国内で意味の近い記事や表現を一つのイシューにまとめ、ユニーク記事数と媒体の多様性を基準に国別TOP 5を計算する。利用者は同じ日付に各国が何を重要視したかを国タブで切り替えて確認する。

本プロジェクトは、次を目的とする非商用ポートフォリオである。

1. モバイルとPCからURLでアクセスできるレスポンシブWebサービスを制作・配布する。
2. 設計・開発・テスト・配布の履歴をGitHubで公開する。
3. データが毎日更新されるサービスを実運用する。
4. 多言語処理、LLM構造化出力、バッチ/API分離、Webアクセシビリティ・キャッシュ、CI/CDの能力を示す。

Androidアプリは廃止しない。Web MVPと公開URLの安定化後に、同じ`/api/v1`契約を利用する後続の選択トラックとして保留する。現在のローカルMVPと初回公開範囲にはAndroid実装・Google Play配布を含めない。

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

- GitHub Pagesのresponsive Web pageと公開JSONへ一つのHTTPS URLから外部アクセスできる。
- 最低2か国の結果を毎日自動更新する。
- 直近7日間の国別TOP 5と根拠記事を確認できる。
- ブラウザキャッシュで最後の正常データを表示できる。

| 指標 | 目標 |
|---|---:|
| 直近30日のバッチ公開成功率 | 95%以上 |
| Pages・公開JSON可用性の内部目標 | 99%以上 |
| 静的JSON応答時間目標 | 500ms以内 |
| 最終正常データ | 48時間以内 |
| 国別の正常推奨サンプル | 30件以上 |
| 国別の公開可能サンプル | 15件以上 |
| イシュー抽出成功率 | 80%以上 |

### 初回リリースに含むもの

- 国別収集、整形、重複排除、イシュークラスタリング、TOP 5
- 直近7日分のJSON公開、ローカル・後続用FastAPIと共通Schema
- レスポンシブWebのタイル/クラウド、詳細、ブラウザキャッシュ
- 部分成功、遅延、メンテナンス、エラー状態
- モバイル・デスクトップ対応の正式Web UI
- 自動レビューとMarkdown障害レポート
- GitHub Actions予約batch・検証・Pages配布、GitHub Pages HTTPS

### 初回リリースの対象外

- ログイン、コメント、広告、決済、パーソナライズ推薦
- サーバー同期型お気に入り、プッシュ通知
- VPS・EC2運用配布、Android・iOSネイティブアプリ、Google Play配布、7日を超える履歴、リアルタイムストリーミング

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
| F-10 | 定期実行 | GitHub Actions scheduleと制限付き再試行、後続systemd timer互換 |
| F-11 | 日付照会 | 直近7日間の利用可能日を提供 |
| F-12 | 国切替 | 同一日付の国別結果を即時切替 |
| F-13 | イシュー可視化 | TOP 5を基本タイル型またはクラウド型で切替表示 |
| F-14 | 詳細 | 統計、代表記事、原文リンク |
| F-15 | オフライン | ブラウザキャッシュで最後の正常結果を表示 |
| F-16 | サービス設定 | メンテナンス、バージョン、告知、ポリシーURL |
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
- 日次公式発表量を考慮し、国別5件以上を部分成功、15件以上を完全成功の収集基準として使う。
- 登録sourceは公式RSS・公共APIのみを使用し、民間news HTMLと政策ブリーフィングの終了済みRSSは使用しない。
- ソースごとの利用条件確認日と許可フィールドを設定へ記録する。
- 利用条件は90日ごとに再確認し、承認・登録・app IDが必要なsourceは確認前に無効とする。

```yaml
US: Federal Reserve RSS；BLS RSSは自動request 403のため無効、BEA APIは登録後に有効化
JP: BOJ RSS；METI Atomは更新停止のため無効、e-Stat APIはapp ID登録後に有効化
KR: 韓国銀行RSS、金融委員会の報道資料・報道説明RSS、中小ベンチャー企業部の報道資料RSS
```

基本許可fieldはRSSが直接提供するtitle・短いsummary・原文URL・媒体・公開時刻とする。BOJ・BOK・金融委員会・中小ベンチャー企業部は保守的にtitle・URL・媒体・公開時刻だけを使う。金融委員会の報道説明RSSは一般報道資料を補完する補助sourceとして使う。記事本文、PDF・添付file、画像、HTMLを解析したsummaryは収集・再配布しない。実URLと承認状態は`config/sources.example.yml`を基準とし、条件付き無効sourceの登録・承認・Secret・検証手順は`docs/SOURCE_REGISTRATION_GUIDE.md`に従う。

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

論理API契約の基本pathは`/api/v1`とする。ローカルと後続VPS/EC2ではFastAPI endpointとして提供し、GitHub Pagesの初回運用では同じresponse Schemaを`data/v1/.../*.json`静的pathへ公開する。Web UIはpathを直接参照せずDataSource interfaceを使う。

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
- Pages modeでは静的JSONだけを読み、外部service keyをbrowserへ露出しない。
- VPS/EC2 API modeではnginxまたは同等gatewayのrate limitを適用する。

---

## 9. Web UI設計とAndroid保留

| 区分 | 選定 |
|---|---|
| 言語/UI | Semantic HTML、CSS、Vanilla JavaScript |
| 構造 | UI → 状態/Service module → IssueDataSource → Browser cache |
| ネットワーク | 標準`StaticJsonDataSource`、後続`ApiDataSource` |
| 保存 | localStorage（表示設定）、Cache APIまたはIndexedDB（直近の正常応答） |
| 対応環境 | 最新Chrome、Edge、Safari、Firefoxのmobile・desktop |
| 初回配布 | GitHub Pagesが静的Webと生成JSONを同じHTTPS originで提供 |
| 後続配布 | 設定でVPS/EC2 FastAPI `/api/v1`を選択し、必要時にCORS適用 |
| Android | 公開Web安定化後に再検討する保留track |

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
| 状態保存 | 初回アクセスはタイル型。以後は最後の選択をlocalStorageへ保存し、再アクセス時に復元 |
| 共通タイトル | `今日のイシューTOP 5` |
| 共通情報 | 分析記事数とデータ生成/更新時刻 |
| 下部領域 | 最終更新時刻と更新ボタンのみ |
| 詳細遷移 | タイルまたはクラウドのキーワードから同一の詳細画面へ遷移 |

タイル型は順位、イシュー名、記事数を各タイルに表示する。1位を最大とし、残りは重要度でサイズと明度を変える。タイル全体をタッチ領域とする。

クラウド型は同じTOP 5を横書きで配置し、`article_ratio`で文字サイズと明度を変える。回転・重なりを避け、キーワードから関連記事を開ける案内を表示する。順位と正確な記事数はアクセシビリティ説明と詳細画面で確認できるようにする。

表示切替ではデータ再取得・再集計を行わず、同一Web状態を別DOMコンポーネントで描画する。国・日付・ロード・エラー状態とスクロール位置を維持する。

```text
IssueHomePage
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

### Android後続保留トラック

- `android/` directoryとAndroid設計記録は削除せず、保留状態で維持する。
- 現在のWeb MVPではAndroid実装、SDK導入、Emulator検証、AAB生成、Google Play提出を完了条件にしない。
- 公開URLとWeb APIの安定化後、ユーザーが再開を決定した場合は同じ`/api/v1`契約とUI動作を再利用する。
- 再開時にKotlin、Compose、Retrofit、Room、DataStore候補を再検証し、別途ADR・日程・費用・Play policyを確定する。

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
│   ├── src/data/
│   │   ├── issue-data-source.js
│   │   ├── static-json-data-source.js
│   │   └── api-data-source.js
│   └── public/data/v1/
├── config/
├── deploy/
├── docs/
│   ├── AI_DEVELOPMENT_GUIDE.md
│   ├── AI_DEVELOPMENT_GUIDE_JA.md
│   ├── DEVELOPMENT_STATUS.md
│   ├── DEVELOPMENT_STATUS_JA.md
│   ├── daily/
│   │   ├── TEMPLATE.md
│   │   └── YYYY-MM-DD.md
│   ├── review/
│   │   ├── WEEKLY_REVIEW_GUIDE.md
│   │   └── WEEKLY_REVIEW_TEMPLATE.md
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

JSONをSQLite/PostgreSQLへ変更してもRouter、Service、Web API契約、保留中のAndroid API契約を維持する。正式Web UIは静的HTML/CSS/Vanilla JSで作り、DataSourceに関係なく同じresponse Schemaと状態定義を使う。標準設定は`DATA_MODE=static`、`DATA_BASE_URL=./data/v1`で、後続serverでは`DATA_MODE=api`、`API_BASE_URL=https://.../api/v1`へ切り替える。mobile-first responsive layout、アクセントカラー一色、簡潔なクラウドデザインを適用する。生成した運用JSONはPages配布artifactへ含めるがsource branchへcommitしない。

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

初回運用はGitHub ActionsのJST timezone scheduleで実行し、workflow concurrencyで重複実行を防ぐ。予約実行は遅延し得るため定刻依存logicを置かず、手動`workflow_dispatch`復旧経路を提供する。公開repositoryの長期非activityによるschedule停止可能性を運用点検へ含める。後続VPS/EC2では同じpipeline entryをsystemd timerの`Persistent=true`とOS file lockで実行する。両modeとも公開済み日付は原則skipする。

```text
python -m app.batch.pipeline_entry
python -m app.batch.pipeline_entry --date 2026-07-29
python -m app.batch.pipeline_entry --dry-run
python -m app.batch.pipeline_entry --force
python -m app.batch.pipeline_entry --countries US,JP
```

`--dry-run`は公開ファイルを変更しない。`--force`は新結果の検証成功時のみ置換する。lock取得失敗は`skipped_locked`として記録する。障害レポートには実行ID、失敗国/段階、例外、原因分類、影響、再試行、改善案3件、マスキング済みスタックを記録する。一国の失敗と期限切れ削除失敗は、可能なら全体を中断させない。

---

## 12. セキュリティ・プライバシー・Web配布とAndroid保留

### アプリとサーバー

- ログイン、広告、位置情報・連絡先・写真・ストレージ権限を使用しない。
- Webは端末権限を要求せず、CSP、HTTPS、安全な外部link policyを適用する。
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

### Android再開時のGoogle Play

以下は現在のWeb MVP範囲外であり、Android track再開時に再検証する。

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

### Android（保留track）

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
- Android再開時にタイル型・クラウド型・各状態のCompose screenshot回帰test

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

### 週完了検知自動レビュー

- 実行：active週の実装・test・文書・`scripts/verify-all.ps1`成功を検知した直後に1回
- 重複防止：同じ週次候補SHAは1回だけreviewし、Critical/High修正でSHAが変わった場合だけ再検証する。
- 範囲：前回レビュー以降のcommit/diff、関連テスト・ビルド・静的検査
- 評価：セキュリティ、正確性、性能、保守性、テスト十分性、文書・アーキテクチャ準拠
- 結果：ローカル専用`reviews/YYYY-MM-DD-weekly-review.md`
- 詳細基準とtemplate：`docs/review/WEEKLY_REVIEW_GUIDE.md`、`docs/review/WEEKLY_REVIEW_TEMPLATE.md`

| 項目 | 確定基準 |
|---|---|
| review時間 | 最大60分 |
| Critical/High修正時間 | review後の別枠で最大90分 |
| command timeout | 基本・Web全体20分、Android再開時は全体30分 |
| 一時的失敗の再試行 | 原因確認後1回 |
| 同一finding修正試行 | 最大2回、以後`BLOCKED` |
| 変更コードcoverage | Line 80%、Branch 70% |
| 全体coverage | Backend 80/70、Web 75/65、Android再開時70/60（Line/Branch） |
| 主要経路 | Backend集計・Repository 90% Line、Web状態・API・cache 80% Line、Android再開時ViewModel・Repository 80% Line |

review範囲はローカル`reviews/.last-reviewed-sha`から現在`HEAD`までとし、正常完了時だけ基準SHAを更新する。初回はリポジトリ全体のsecurity・設定と直近7日diffを確認する。diff外の既存問題は`LEGACY`とするが、Critical/Highは修正する。

必須検査は仕様同期、diff形式、secret・security、依存関係脆弱性、`scripts/verify-all.ps1`、coverage、正確性・性能・保守性・architectureの順に行う。LLMまたはUI変更時は対応する回帰検査を追加する。性能は同一ローカル環境3回の中央値で、cache API p95 500ms、fixture非cache API p95 1秒、mock 3か国pipeline 60秒を基準とする。

LLM変更時はSchema 100%、入力外article ID・根拠0件、国間混在0件、TOP 5重複0件、順位決定性100%、抽出成功率80%以上を要求する。labelは国別最大5件のsampleで80%以上が受容可能であること。

| 重大度 | 対応 |
|---|---|
| Critical | 安全に即時修正・再検証し、`RESOLVED`と根拠を残す。修正不能なら`UNRESOLVED/BLOCKED`。 |
| High | Criticalと同様に修正・再検証して状態を記録。 |
| Medium | 自動修正せず、ファイル・行・影響・推奨対応を履歴化。 |
| Low | 自動修正せず、改善候補として履歴化。 |

review最終状態は`PASS`、`PASS_WITH_FINDINGS`、`FAIL`、`BLOCKED`のいずれかとする。finding IDは`WR-YYYYMMDD-NNN`形式とし、同じfile・rule・原因はfingerprintで重複生成を防ぐ。Mediumが3回、Lowが4回連続で未解決の場合は優先検討対象とするが、期間だけでseverityを自動昇格しない。

`reviews/`は`.gitignore`へ含め、レビューMDはローカルだけに保存する。Critical/High修正は`codex/review-fix-YYYY-MM-DD` branchで検証し、明確な修正commitとDraft PRで`main`へ反映する。ローカルreviewへ`RESOLVED`、修正commit SHA、PR番号を記録する。Critical/Highがなければbranch・commit・PRを作らずローカルreviewだけを残す。外部契約、資格情報、利用者判断が必要な項目を勝手に回避しない。

---

## 14. 配布と運用

```text
初回運用
GitHub Actions schedule/workflow_dispatch
  → 収集・LLM・集計・Schema検証
  → 静的Web + data/v1 JSON artifact
  → GitHub Pages HTTPS

後続運用
Internet → nginx/ALB → FastAPI/uvicorn
VPS/EC2 systemdまたはcontainer scheduler → 同じbatch entry
```

- 初回Pages配布は公式Pages artifact方式で行い、生成JSONを`main`へ自動commitしない。
- PRはmock・fixtureだけで検証し、実ニュース・LLM Secretは保護された予約/手動運用workflowだけで利用する。
- 生成またはSchema検証に失敗した場合は既存Pages配布を維持し、失敗artifactを公開しない。
- Pages artifactには直近7日の公開可能JSON、静的Web、policy pageだけを含める。
- VPS/EC2後続配布は初回設定と反復配布を分離し、`/health`、`/ready`、rollback、直近2 release保管を適用する。

運用指標は、batch時間、国・source別記事数/失敗率、LLM呼出・token・費用・再試行・成功率、Actions実行・Pages配布成否、最終公開成功時刻、後続API modeのrequest数・error率・応答時間とする。24時間遅延で案内、48時間遅延でWeb警告を表示する。運用RunbookにはActions予約遅延・無効化、手動再実行、Pages artifact rollback、source認証/形式変更、LLM費用急増、JSON復旧を含める。VPS/EC2再開時にservice再起動、証明書障害、server rollbackを追加する。

---

## 15. GitHubとCI/CD

Git除外対象：

```text
.env
.env.*（`.env.example`を除く）
secrets/
credentials/
*.jks
*.keystore
*.p12
*.pfx
*.pem
key.properties
keystore.properties
google-services.json
*service-account*.json
firebase-adminsdk*.json
local.properties
data/
reports/
reviews/
logs/
*.log
*.db
*.sqlite*
.vscode/settings.json
.vscode/launch.json
```

### ファイル別Secret管理

| ファイル・領域 | 想定される機密情報 | 開発環境の保存先 | 運用環境の保存先 | Gitポリシー |
|---|---|---|---|---|
| `backend/.env` | ニュースAPI key、NAVER Client ID/Secret、LLM key、DB URL、JWT/Admin Secret | ローカルの非追跡ファイル | 初回GitHub Environment Secrets、後続`/etc/country-issue-cloud/backend.env`またはcloud Secret | commit禁止 |
| `backend/.env.example` | 環境変数名と非機密の例 | repository | repository | 実値なしでcommit可 |
| `backend/app/config.py` | 環境変数Schemaと検証規則 | repository | 配布code | 値のhardcode禁止、変数名のみ可 |
| `android/local.properties` | SDK pathとローカル設定 | 開発者PC | 対象外 | commit禁止 |
| `key.properties`、`keystore.properties`、`*.jks`、`*.keystore` | アプリ署名keyとpassword | Git外で暗号化保管 | Play App Signing/CI Secret | commit禁止 |
| Android `BuildConfig`、`strings.xml`、Kotlin source | backend URL、誤入力されたprovider key | 公開可能なURLのみ含める | AAB/APKに含まれる | 外部API/LLM keyとClient Secret禁止 |
| `google-services.json`、service account JSON | Firebase client設定または管理者credential | 必要時に別経路で共有 | hosting Secret | 原則commit禁止、service accountは絶対禁止 |
| `.github/workflows/*.yml` | ニュース・LLM・Pages・後続配布credential | `${{ secrets.NAME }}`参照 | GitHub Environment Secrets | 平文値・PR Secret露出禁止 |
| Pages配布artifact `data/v1/` | 公開issue resultと記事metadata | CI一時workspace | GitHub Pages | 公開可能fieldのみ、Secret・本文・raw log禁止 |
| `deploy/`、Docker、systemd設定 | DB password、API key、SSH key | 変数参照のみ保存 | server環境変数・Secret保存先 | 平文値禁止 |
| `tests/fixtures/`、`sample-data/` | 実responseのtoken、header、執筆者の個人情報 | 匿名化したmock/fixture | 対象外 | 加工dataのみ可 |
| `logs/`、`data/`、`*.db`、日報・review | 認証header、IP、device情報、raw response | ローカル専用・mask処理 | access制限付き保存先 | raw機密情報のcommit禁止 |
| `.vscode/launch.json`、IDE実行設定 | 実行環境変数とtoken | 開発者PC | 対象外 | 機密値を含むファイルはcommit禁止 |

Android binaryはreverse engineering可能であると仮定する。`API_BASE_URL`と公開用OAuth Client IDだけをアプリへ含められ、ニュースAPI key、LLM key、NAVER Client Secret、DB credential、管理者token、JWT署名key、署名passwordはbackendまたは配布Secretだけに保存する。Client IDもprovider policyで機密扱いの場合はserver専用とする。

### commitブロック基準

- `scripts/check-secrets.ps1`でGit追跡ファイル名と信頼度の高いsecret patternを検査し、`scripts/verify-all.ps1`の必須stepとして実行する。
- `.env.example`には変数名、空値、明白なplaceholderだけを許可する。実keyに似た例を使用しない。
- 機密ファイル、private key、provider token、credentialを検出した場合は検証とcommitを失敗させる。
- log、fixture、文書、screenshotへ`Authorization`、cookie、個人識別情報、外部response全体を含めない。
- PR CIでも同じ検査とGitHub secret scanning/push protectionを使う。ローカル検査はserver側保護の代替ではない。
- 疑わしい値をallowlistで回避せず、保存先をSecret保存先へ変更する。例外には利用者承認とADRを必要とする。
- 漏えいしたkeyはGitから文字列を削除するだけで解決したとみなさない。直ちに無効化・再発行し、影響範囲を確認して必要ならrepository履歴を整理する。

READMEにはアプリ/Webリンク、スクリーンショット、アーキテクチャ、技術選定、実行方法、API例、テスト、出典・LLM・運用ポリシーを含める。MIT License、secret scanning、依存関係更新、Issue/PRテンプレートを使う。

Pull Request CI：

- 共通：韓国語・日本語仕様の同時変更と主要構造の同期検査
- Python：Ruff、mypy、pytest、import境界、セキュリティ検査
- Android（保留）：track再開時のみktlint、detekt、Android Lint、test、debug build
- Web：静的検査、JS test、DataSource契約、基本accessibility検査
- Pages：fixture基盤build、公開artifact Secret検査、link・JSON Schema smoke test

```text
main merge → merge済みmainの全CI・ローカルsmoke再検証 → fixture Pages preview/build検証
保護されたschedule/workflow_dispatch → 実batch → Schema・Secret検査 → Pages artifact配布 → 失敗時は既存配布を維持
VPS/EC2再開後 → ApiDataSource設定 → server配布 → health/ready → 失敗時rollback
v* tag → Pages URL検証 → GitHub Release。Android再開後のみAABとPlay内部test trackを追加する。
```

### AI開発ガードレール

- 実装作業は目標、範囲、対象外、完了条件、検証command、週次commitを含む作業契約に従う。
- `docs/AI_DEVELOPMENT_GUIDE.md`と日本語版をAI作業の実行基準とする。
- `docs/DEVELOPMENT_STATUS.md`と日本語版へ現在目標、完了commit、検証結果、次作業、外部依存を記録する。
- 開発作業を行った日は終了時に`docs/daily/YYYY-MM-DD.md`を作成する。一つのファイルへ韓国語・日本語を併記し、目標の最終commitとPRへ含める。
- 共通完了条件に機能・エラー経路、関連test、lint/type/build、秘密情報検査、文書同期、日本語コメント規則を含める。
- 週次commit前に`scripts/verify-all.ps1`を実行し、仕様同期と各project検査を一つの入口で行う。
- 週次branchの一時WIP commitは許可するが、週完了検知review後にsquashまたはamendし、週次commit一つへ整理する。
- 各開発週は指定された`codex/week-*` branchで進め、`main`対象のDraft PR一つとして公開する。
- 統合検証、CI、review通過後にReadyへ変更し、**Rebase and merge**でmergeして検証済み週次commit subjectと線形履歴を維持する。
- `Create a merge commit`は使わない。ローカルWIPのsquashができなかった例外時だけ`Squash and merge`を許可し、squash commit subjectを日付・3言語形式で手動指定する。
- 目標変更を`main`へ直接pushしない。
- merge後、最新`main`で`scripts/verify-all.ps1`と利用可能なローカルsmoke testを再実行し、merge conflict、依存関係の組合せ、統合errorを確認する。
- merge後検証の成功を対象週の完了条件とする。失敗時は`codex/post-merge-fix-week-<number>` branchと別PRで修正し、`main`を直接変更しない。
- merge後検証の成功後に週次branchを削除し、検証済みの最新`main`から次週branchを作る。
- AIがAPI契約、主要architecture、技術stack、費用・公開範囲を変える場合はADRと利用者確認が必要。
- UI screenshot基準変更は自動承認せず、人が意図された変更か確認する。

---

## 16. コスト計画

| 項目 | ポリシー |
|---|---|
| Google Play | 1回限りの登録料を計上 |
| GitHub Pages | 公開portfolio用途と無料提供量内で運用 |
| VPS/EC2・ドメイン | 後続移行時のみ低価格の月額固定費と予算を事前確定 |
| NewsAPI | 運用利用せず、ローカル開発のみ |
| 運用ニュースソース | 無料・利用可能なソース優先 |
| LLM | 月額USD 10上限 |
| HTTPS | 初回Pages標準HTTPS、後続は無料証明書またはcloud証明書 |
| GitHub Actions | 公開repositoryの標準runnerと無料提供量内、larger runner禁止 |

外部サービス料金と規約は本番配布直前に再確認する。

---

## 17. 開発スケジュール

2026年8月3日月曜日に開始する、AI開発支援前提のローカル優先日程である。fixture、ローカルFastAPI、browserで開発し、3週間以内にGitHub Actions + GitHub Pagesのresponsive Web MVPを公開する。FastAPIとApiDataSourceは後続VPS/EC2互換境界として維持するが、server契約・配布は現在の完了条件から除外する。日付別表はbaselineとして維持するが作業を前倒しできる。reviewは固定曜日ではなく各週の実装・test・文書・全検証完了を検知した直後に実行する。土日は遅延吸収と利用者確認のbufferとする。Android・Play連携は別途再開決定後のみ日程化する。

### 日次開発レポートポリシー

- 保存先：`docs/daily/YYYY-MM-DD.md`（`Asia/Tokyo`基準）
- 形式：`docs/daily/TEMPLATE.md`を使用し、一つのファイルに同等の韓国語・日本語sectionを記述する。
- 内容：本日の目標、実施作業、主な変更ファイル、検証結果、決定事項、問題・risk、次作業
- 失敗・未完了作業も原因と次の対応を含めて記録する。
- 秘密鍵、token、認証header、個人情報、raw log全体を含めない。
- Git追跡対象として週次branchへ保存し、日次専用commitを作らず対象週の最終commitとPRへ含める。
- 週完了検知reviewの`reviews/*.md`は引き続きローカル専用とし、日次reportと混在させない。

### 週別目標

| 週 | 期間 | 対象目標 | 完了基準 |
|---|---|---|---|
| 1週目 | 8/3～8/8 | 1 環境・骨格、2 データ・API、3 収集・整形 | ローカルAPIと3か国収集基盤が動作 |
| 2週目 | 8/10～8/15 | 4 LLM・TOP 5、5 batch・Web基盤 | 国別TOP 5をbatch→静的JSON/FastAPI→Webで実演 |
| 3週目 | 8/17～8/22 | 6 Web UI、7 cache・accessibility、8 Pages公開 | 実URLと自動更新を検証し`v0.8.0-pages-mvp`を公開 |

### 1週目 — 基盤、ローカルAPI、国別収集

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/3(月) | 環境、monorepo、設定分離、fixture、CI、AI開発検証入口 | 目標1検証後、目標commit templateを適用 |
| 8/4(火) | データモデル、Schema、JSON Repository | fixture・Repositoryテスト |
| 8/5(水) | アトミック保存、保管、FastAPI | 目標2中間検証、commitなしで週次branchを維持 |
| 8/6(木) | Collector、fixture/実ソース、重複排除 | 契約・重複排除テスト |
| 8/7(金) | 国別並列収集、失敗隔離、データモード | 1週目全検証後に候補commit・Draft PR |
| 8/8(土) | 1週目の遅延吸収・利用者確認buffer | 未完了項目がある場合だけ補完 |

### 2週目 — LLM、全体batch、Web基盤

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/10(月) | LLM interface、mock、構造化出力、実adapter | mockと限定実呼出検証 |
| 8/11(火) | 国内cluster、根拠検証、決定的TOP 5 | 統合・幻覚防止・同順位テスト |
| 8/12(水) | cache、timeout/retry、token/費用 | 目標4中間検証、commitなしで週次branchを維持 |
| 8/13(木) | pipeline、部分成功、lock、retry、report | 失敗・重複実行・maskテスト |
| 8/14(金) | 静的JSON publisher、DataSource基盤Webと統合実行 | 2週目全検証後に候補commit・Draft PR |
| 8/15(土) | 2週目の遅延吸収・利用者確認buffer | 未完了項目がある場合だけ補完 |

### 3週目 — Responsive Web UI、cache、Pages公開

| 日付 | 開発内容 | 成果物・検証 |
|---|---|---|
| 8/17(月) | IssueDataSourceの2 adapter、responsive基本画面 | static/API契約と基本画面test |
| 8/18(火) | 国・日付選択、C案tile、A案cloud、詳細 | 表示・切替・詳細flow test |
| 8/19(水) | localStorage、Cache API/IndexedDB、error・accessibility | cache復旧・keyboard・拡大検証 |
| 8/20(木) | Actions schedule/manual workflow、concurrency、Pages配布 | fixture artifactと失敗時の既存配布維持を検証 |
| 8/21(金) | 全回帰、Secret検査、README・screenshot・Release候補 | 週次候補commitとDraft PR作成 |
| 8/22(土) | 最終遅延吸収・release確認buffer | 未完了項目がある場合だけ補完 |

### 週単位commit・PR policy

目標1 scaffoldは別PRで完了済みであり、残り開発は次の3週単位で管理する。

| 週 | 作業branch | 対象目標 | 最終commit message |
|---|---|---|---|
| 1週目 | `codex/week-01-data-collection` | 2 data・API、3 国別収集 | `YYYY/MM/DD feat: implement local data and collection`<br>`로컬 데이터와 국가별 수집 구현`<br>`ローカルデータと国別収集を実装` |
| 2週目 | `codex/week-02-pipeline-publishing` | 4 LLM・TOP 5、5 batch・静的公開 | `YYYY/MM/DD feat: complete issue pipeline and static publishing`<br>`이슈 파이프라인과 정적 게시 완성`<br>`イシューパイプラインと静的公開を完成` |
| 3週目 | `codex/week-03-pages-mvp` | 6 Web UI、7 cache・accessibility、8 Pages公開 | `YYYY/MM/DD release: publish GitHub Pages MVP`<br>`GitHub Pages MVP 공개`<br>`GitHub Pages MVPを公開` |

各週はbranch一つ、最終commit一つ、Draft PR一つを使う。週の範囲が完了した直後に候補commitを作り、自動reviewを実行する。Critical/High修正は同じcommitへamendして`--force-with-lease`で更新する。Medium/Lowはローカルreview履歴だけを残す。CI・review通過後に**Rebase and merge**し、merge直後の最新`main`で全検証とsmoke testが成功した場合だけ対象週を完了とする。

### 後続選択日程 — VPS/EC2移行

| 営業日 | 内容 | 完了基準 |
|---|---|---|
| 1日目 | VPSまたはEC2、domain、非root/IAM、firewall | 基本server・cloud security確認 |
| 2日目 | nginx、TLS、FastAPI systemd | HTTPS APIアクセス |
| 3日目 | バッチservice/timer、運用環境変数 | 手動・予約バッチ成功 |
| 4日目 | server配布workflow、health/ready、rollback | 配布・検証・rollback訓練 |
| 5日目 | `DATA_MODE=api`切替、CORS/CSP、主要画面smoke test | UI logic変更なしで運用API接続 |
| 以後7日 | 自動バッチ、費用、エラー、品質観察 | 7日連続運用記録 |

### Android再開決定後の別日程 — Playテストとリリース

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
v0.6.0 Web基盤と全体pipeline
v0.7.0 Responsive Web主要UI
v0.8.0 オフラインと安定化
v0.9.0 公開Web配布と運用検証
v1.0.0 初回公開リリース
```

---

## 19. リリースゲート

- [x] 収集が特定テーマ検索へ偏っていない
- [x] 最低2か国の運用ソース利用条件確認
- [ ] 7日連続自動バッチ結果
- [x] 一国失敗時に他国結果を維持
- [x] LLM結果に存在しない記事/表現なし
- [x] API 200/400/404/503検証
- [x] Web browser cache・復旧検証
- [ ] 公開Web URLで主要画面とAPIが動作
- [x] プライバシー、問い合わせ、出典、公開日表示
- [x] GitHubに秘密鍵・運用データなし
- [x] Pages配布失敗時の既存正常artifact維持・rollback検証
- [ ] VPS/EC2再開時のserver rollback検証
- [ ] Android再開時にPlay申告・テスト要件充足
- [x] READMEでアプリ/Web/設計/テストを確認可能

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
| Actions予約遅延・無効化 | 定刻非依存、手動実行、最後の正常Pagesを維持 |
| 後続VPS/EC2障害 | health monitor、systemd/container、cache、rollback |
| Android再開後のPlay審査遅延 | 再開時にpolicy資料と日程bufferを再算定 |
| 公開リポジトリ鍵漏洩 | `.gitignore`、secret scan、鍵rotation |

---

## 21. 最終成果物

- [ ] 統合仕様、画面/機能/アーキテクチャ設計とADR
- [x] データ・出典ポリシーとAPI仕様
- [x] PythonバッチとFastAPI
- [x] Responsive Web application
- [x] Android後続track保留記録
- [x] 自動テストとCI/CD
- [x] GitHub Actions batch・Pages配布workflow
- [ ] 後続VPS/EC2用配布script、nginx、systemd/container template
- [ ] 運用Runbookと障害レポート例
- [x] プライバシーポリシーと問い合わせページ
- [ ] Android再開時にGoogle Play登録資料
- [ ] README、デモ画像、GitHub Release
- [ ] 開発日ごとの韓国語・日本語併記日次report

---

## 22. 最終定義

> 国別イシュークラウドは、米国・日本・韓国の経済ニュースを国別に独立収集し、LLMで各国内の類似した記事表現をイシュー単位へまとめ、ユニーク記事数と媒体多様性に基づく国別TOP 5をURLで表示するresponsive Web serviceである。結果には実際の出典とサンプル数を提示し、batch失敗、cache復旧、外部API費用などの運用課題を明示的に処理する。Androidアプリは公開Web安定化後に選択的に再開できるよう、API契約と設計記録を保全する。
