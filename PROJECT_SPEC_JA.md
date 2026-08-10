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

毎日、米国・日本・韓国の報道機関の経済ニュースを国別に150件収集することを目標とし、最大250件まで独立収集する。titleと提供された短いsummaryから反復出現する名詞・複合名詞候補を抽出し、同義表現を一つのkeywordへまとめて、ユニーク記事数と媒体多様性に基づく国別keyword TOP 5を計算する。利用者はkeywordから該当keywordの根拠記事一覧を確認する。

本プロジェクトは、次を目的とする非商用ポートフォリオである。

1. モバイルとPCからURLでアクセスできるレスポンシブWebサービスを制作・配布する。
2. 設計・開発・テスト・配布の履歴をGitHubで公開する。
3. データが毎日更新されるサービスを実運用する。
4. 多言語処理、LLM構造化出力、バッチ/API分離、Webアクセシビリティ・キャッシュ、CI/CDの能力を示す。

Androidアプリは廃止しない。keyword中心Webと公開URLの安定化後に、`/api/v2`契約を利用する後続の選択トラックとして保留する。現在のローカルMVPと初回公開範囲にはAndroid実装・Google Play配布を含めない。

### 利用者価値

- 同じ日付の3か国の経済的関心を素早く比較できる。
- 一般語を除外し、類似表現をまとめた意味ある単語・複合名詞keywordを確認できる。
- 記事数、媒体数、最大20件の関連記事から選定根拠を確認できる。
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
| 国別収集目標 | 重複排除後150件 |
| 国別配布可能サンプル | 70件以上 |
| 国別部分成功サンプル | 50～69件 |
| keyword処理成功率 | 80%以上 |

### 初回リリースに含むもの

- GDELT中心の国別ニュース収集、整形、重複排除、言語別keyword抽出・clustering、TOP 5
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
米国経済ニュース150件目標 → 米国keyword TOP 5 → keyword別関連記事
日本経済ニュース150件目標 → 日本keyword TOP 5 → keyword別関連記事
韓国経済ニュース150件目標 → 韓国keyword TOP 5 → keyword別関連記事
```

- 共通テーマを先に決めて3か国で検索しない。
- 一国の失敗が他国の処理・表示を妨げない。
- イシュー名は原語を基準とし、米国・日本には韓国語補助名を付けられる。
- 補助翻訳は集計・順位に使わない。
- 記事にない表現を根拠として生成しない。
- 言語別分析器が反復名詞と最大2形態素の短い複合名詞を抽出し、LLMは候補外表現を作らず選択的同義語統合だけを担当する。画面labelは文断片ではなく一つのイシュー概念を優先する。
- 順位はユニーク記事数、ユニーク媒体数、最新時刻、`issue_id`の順でコードが計算する。
- 公式APIまたは公開RSSのみを使用し、本文全体と画像を保存しない。
- APIとバッチは相互の実行モジュールをimportせず、公開JSONだけで通信する。
- 一時ファイル作成、Schema検証、アトミック置換の順で結果を公開する。

---

## 4. 機能要件

| ID | 機能 | 説明 |
|---|---|---|
| F-01 | 国別収集 | GDELT主sourceから国別150件目標・最大250件の経済ニュースを独立収集 |
| F-02 | 整形・重複排除 | URL、タイトル、類似度で国内重複を排除 |
| F-03 | keyword抽出 | 英語・日本語・韓国語別の反復名詞と最大2形態素の短い複合名詞を抽出し、一般語・文断片を除外 |
| F-04 | keyword統合 | 国内の同義語・表記揺れを根拠表現内で統合 |
| F-05 | TOP 5 | keyword別ユニーク記事数と媒体数で決定的順位を算出 |
| F-06 | 結果保存 | 日付JSONとlatestをアトミック保存 |
| F-07 | 品質レビュー | サンプル、偏り、抽出率、ラベルを点検 |
| F-08 | 障害レポート | 原因、影響、改善案、スタックを記録 |
| F-09 | 保管 | 結果7日、レポート90日、ログ30日 |
| F-10 | 定期実行 | GitHub Actions scheduleと制限付き再試行、後続systemd timer互換 |
| F-11 | 日付照会 | 直近7日間の利用可能日を提供 |
| F-12 | 国切替 | 同一日付の国別結果を即時切替 |
| F-13 | イシュー可視化 | TOP 5を基本タイル型またはクラウド型で切替表示 |
| F-14 | 詳細 | keyword統計、関連記事最大20件、原文リンク |
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
| 国別目標 | 重複排除後150件 |
| 国別最大数 | 250件 |
| 正常 | 70件以上、keyword 5件 |
| 部分成功 | 50～69件、配布しない |
| 単一媒体の最大反映 | 収集結果の20%または30件の小さい方 |
| 媒体偏重警告 | 30%超 |
| 重大な偏重 | 50%超 |

100件以上を推奨収集目標として維持するが、国別の配布下限は70件とする。適法性と透明性を優先し、実際の収集・重複排除後の記事数を画面に表示し、下限を満たすために24時間範囲を任意に延長しない。

### 出典ポリシー

- GDELT Project DOC API Article Listは長期的な主source候補だが、反復HTTP 429が確認されている間は運用設定で無効とする。制限付き単一requestで正常応答と利用条件を再確認した後だけ、`sourcecountry`、`sourcelang`、直前24時間、`maxrecords=250`を国別に独立適用して再有効化する。
- 初回運用のnews sourceは無料構成に固定する。韓国はNAVER API HUB news検索の無料呼出上限内で補完し、有料移行・従量課金拡張は利用者承認前に使わない。
- NAVER呼出はapplicationとNAVER Consoleの両方で日300回・月9,000回に制限し、いずれかの上限到達時に追加呼出を自動停止する。使用量50%・80%で通知し、無料policy変更前は有料超過利用や自動上限拡張を許可しない。
- 米国・日本の経済news補完はNewsData.io Latest News API無料planの`country`・`language`・`business` filterを国別に独立適用する。呼出はapplicationで日40回・月1,200回に制限し、国別目標・上限150件と最大20pageだけを巡回して、有料超過利用と自動有料移行を禁止する。無料planの遅延dataとtitle・link・媒体・公開時刻だけを使用する。
- NewsData.io結果には国別の遮断媒体listを適用し、日本の結果はversion管理された経済関連title用語のいずれかを含む必要がある。株価自動生成・企業決算転載・プレスリリース配信platformのように反復template比率が高い媒体はsampleから除外し、除外件数を診断へ残す。
- 経済範囲はversion管理された国別経済topic query群で制限し、query別収集量と偏りを記録する。特定企業・事件名を事前投入して結果を誘導しない。
- 既存の中央銀行・政府機関RSSと条件付き公共APIは補助sourceとして維持し、主source結果とまとめて重複排除する。
- NewsAPI、GNews、Mediastack、World News APIなど開発専用または有料移行が必要な集約APIは本番依存にしない。
- 報道機関pageのHTMLと記事本文は直接crawlせず、提供API/RSSのtitle・短いsummary・URL・媒体・公開時刻だけを使う。
- GDELT利用結果にはGDELT Project名と公式site linkを表示する。
- ソースごとの利用条件確認日と許可フィールドを設定へ記録する。
- 利用条件は90日ごとに再確認し、承認・登録・app IDが必要なsourceは確認前に無効とする。

```yaml
ALL: GDELT DOC API Article Listは429安定性の再検証まで一時無効
US supplementary: Federal Reserve RSS；BLS RSS無効、BEA API条件付き
JP supplementary: BOJ RSS；METI Atom無効、e-Stat API条件付き
KR supplementary: 韓国銀行・金融委員会・中小ベンチャー企業部RSS
KR news supplement: NAVER API HUBを無料呼出上限内で使用
US/JP news supplement: NewsData.io Latest News API無料planを国別に独立使用
```

GDELT・RSS・NewsData.ioが提供するtitle・短いsummary・原文URL・媒体・公開時刻だけを許可する。記事本文、PDF・添付file、画像、HTMLを解析したsummaryは収集・再配布しない。GDELTとNewsData.io dataは派生keywordと最小記事metadataだけを直近7日保管し、provider attributionを表示する。実endpoint、query version、承認状態は`config/sources.example.yml`を基準とし、詳細手順は`docs/SOURCE_REGISTRATION_GUIDE.md`に従う。

### 重複排除

1. トラッキングパラメータを除去したURLの一致
2. HTML・空白・句読点・大小文字を正規化したタイトルの一致
3. タイトル類似度0.92以上、公開時刻差6時間以内

関連記事一覧はkeyword根拠がtitle・提供summaryに実在する記事だけを含め、ユニーク媒体多様性・新しさ・HTTPS link順で最大20件を選ぶ。

---

## 6. keyword分析、LLMと集計

言語別分析器はtitleから反復名詞と最大2形態素の短い複合名詞を抽出する。韓国語は`kiwipiepy`、日本語は`SudachiPy` core辞書、英語は正規化した単語・2語名詞表現規則に確定する。`経済`、`市場`、`政府`、`発表`、`見通し`、`投資`のように単独でイシューを識別しにくい一般語と国別stopwordをversion管理する。一つのtitleから複数候補を生成するが、画面labelは一つのイシュー概念だけを示し、文頭部分をそのまま候補にしない。

同一記事で一つのkeywordが複数回出現してもdocument frequencyは1件と数える。70件以上の運用sampleで最低4件または全体の5%の大きい方と、異なる2媒体以上を満たす候補だけを順位へ含める。日付・曜日・月/四半期表現、通貨単位、プレスリリース慣用語、発売・決算・株価・移動平均のような反復template一般語を除外する。TOP 5間の関連記事集合Jaccard類似度が0.5以上なら後順位候補を除外し、異なる5イシューを保証する。生の出現回数だけで順位を決めず、転載・類似記事と単一媒体集中を先に除外する。

LLMは翻訳word cloudを作るものではなく、分析器が抽出した候補内で一国内の同義語・表記揺れを選択的に統合する限定的なtoolである。標準運用はLLMなしで決定的に動作し、表示名は原文に存在する短い単語・複合名詞だけを使う。

```text
基準金利据え置き / 金融通貨委員会の金利決定 / 韓国銀行の金融政策
→ 基準金利
```

LLMは国内候補cluster、原語keyword、韓国語補助名、構造化JSONを生成する。入力候補外の表現生成、国をまたぐ統合、順位決定、投資判断は行わない。

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
document_frequency = keywordが1回以上出現したユニーク記事数
publisher_count    = keyword関連のユニーク媒体数
article_ratio      = document_frequency / 国の有効記事数
keyword_score      = document_frequency優先、publisher_count・最新時刻・keyword_id順で同順位解消
```

`success`：3か国がそれぞれ記事70件以上、keyword処理成功率80%以上、keyword 5件をすべて満たす。

`partial_success`：ちょうど2か国だけが上記配布基準を満たす。公開fileは生成しない。

`failed`：配布基準を満たす国が1か国以下。

3か国すべてが配布可能な場合だけ日付結果を保存し、失敗実行では`latest.json`を変更しない。

記事数70件はsample量gateにすぎず、品質通過を意味しない。上記の頻度・媒体・一般語・重複イシュー基準をすべて満たすkeyword 5件を作れない国は失敗とし、新しい公開fileを作成しない。

---

## 7. データSchemaと保管

```json
{
  "schema_version": "2.0",
  "date": "2026-07-29",
  "generated_at": "2026-07-29T08:10:00+09:00",
  "status": "success",
  "countries": {
    "US": {
      "status": "success",
      "article_count": 137,
      "extraction_success_rate": 0.95,
      "top_keywords": [{
        "rank": 1,
        "keyword_id": "us_semiconductor",
        "keyword_label": "semiconductor",
        "display_label_ko": "반도체",
        "document_frequency": 31,
        "publisher_count": 14,
        "article_ratio": 0.226,
        "evidence_expressions": ["semiconductor", "chip industry"],
        "related_articles": [{
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

keyword中心契約は既存イシュー中心`/api/v1`のfield意味を変更せず、`/api/v2`と`data/v2`として追加する。実装前はv1を継続提供し、producer・Static/API DataSource・Webを同一PRでv2へ切り替え、互換期間中はv1を維持する。Web UIはpathを直接参照せずDataSource interfaceを使う。

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
| 後続配布 | 設定でVPS/EC2 FastAPI `/api/v2`を選択し、必要時にCORS適用 |
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
3. keyword詳細と関連記事
4. プロジェクト情報
5. プライバシーポリシー/問い合わせ
6. オープンソースライセンス
7. メンテナンス/更新案内

ホーム画面は、アプリ名/基準日、国タブ、直近7日、`今日のイシューTOP 5`可視化、最終更新時刻、更新ボタンの順とする。国タブは同一日付の応答を利用し、追加リクエストなしで切り替える。日付変更時のみリクエストする。

### ホーム画面UI確定案

TOP 5は一つの可視化領域だけで提供し、同じ5件を下部リストへ重複表示しない。

公開Webは確定済みmobile app sampleを視覚基準として使う。白背景とblue accent、中央title、国tab、横型日付選択、分析記事数・更新時刻、右側tile/cloud segment、TOP 5可視化、下部再読込の順で構成する。mobileでは画面幅を満たし、wide画面では最大幅の中央app panelとして表示する。

| 項目 | 確定動作 |
|---|---|
| 基本表示 | 加重タイル型（C案） |
| 代替表示 | 自由配置イシュークラウド（A案） |
| 切替方法 | 可視化領域右上の`タイル / クラウド`スライド型セグメントボタン |
| 状態保存 | 初回アクセスはタイル型。以後は最後の選択をlocalStorageへ保存し、再アクセス時に復元 |
| 共通タイトル | `今日のイシューTOP 5` |
| 共通情報 | 分析記事数とデータ生成/更新時刻 |
| 下部領域 | 最終更新時刻と更新ボタンのみ |
| 詳細遷移 | タイルまたはクラウドのkeywordから同一keyword詳細と関連記事一覧へ遷移 |

タイル型は順位、keyword、関連ユニーク記事数を各タイルに表示する。1位を最大とし、残りは重要度でサイズと明度を変える。タイル全体をタッチ領域とする。

クラウド型は同じkeyword TOP 5を横書きで配置し、`article_ratio`で文字サイズと明度を変える。回転・重なりを避け、keywordから関連記事を開ける案内を表示する。詳細画面はkeyword根拠表現、ユニーク記事・媒体数、最新順の関連記事最大20件を提供する。

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
- 公開URLとWeb APIの安定化後、ユーザーが再開を決定した場合は同じ`/api/v2`契約とUI動作を再利用する。
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
| ローディング | スケルトンと国・日付・表示方式の入力制限 |
| 本日分未準備 | 最新日へフォールバックし案内 |
| 部分成功 | 該当国へ制限案内 |
| 国別失敗 | 該当国だけ更新遅延を表示 |
| オフライン+キャッシュ | キャッシュと最終確認時刻 |
| オフライン+キャッシュなし | 原因記録、接続案内、再試行button。結果がなければrenderしない |
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
│   └── public/data/v2/
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

JSONをSQLite/PostgreSQLへ変更してもRouter、Service、Web API契約、保留中のAndroid API契約を維持する。正式Web UIは静的HTML/CSS/Vanilla JSで作り、DataSourceに関係なく同じresponse Schemaと状態定義を使う。keyword移行後の標準設定は`DATA_MODE=static`、`DATA_BASE_URL=./data/v2`で、後続serverでは`DATA_MODE=api`、`API_BASE_URL=https://.../api/v2`へ切り替える。mobile-first responsive layout、アクセントカラー一色、簡潔なクラウドデザインを適用する。生成した運用JSONはPages配布artifactへ含めるがsource branchへcommitしない。各実行は現在の公開siteから直前6日分をSchema 2.0で再検証して復元し、当日結果を加えて最大7日だけをatomicに配布する。`main` pushは外部APIを呼ばず、既存公開`latest.json`と日付履歴を復元してWeb codeだけを再配布し、復元失敗時は既存Pages配布を維持する。

管理者確認用として最終選択記事全件のID・title・原文HTTPS URL・媒体・公開時刻と収集診断を別Actions artifactへ保存する。このartifactは7日保持し、PagesとGitへ含めず、Secret、認証header、raw API response、記事本文を含めない。

---

## 11. バッチとスケジューリング

```text
1. OS lock取得
2. 設定とソース確認
3. US/JP/KR並列収集
4. 国別整形・重複排除
5. 国別言語分析器によるkeyword候補抽出・stopword除外
6. 制限付きLLMによる同義語・表示名統合
7. keyword根拠記事検証
8. 国別TOP 5集計
9. 品質レビュー
10. 公開条件判定
11. 一時JSON作成・検証
12. 日付ファイルをアトミック置換
13. latest.json更新
14. 期限切れデータ削除
15. 実行要約とlock解除
```

| 時刻 | 処理 |
|---|---|
| 08:00 | 基本バッチ |
| 08:30 | 結果がない場合の1回目再試行 |
| 09:30 | 最終再試行 |
| 10:00 | 状態確認と連続失敗通知候補 |

初回運用は毎日09:00 JST/KST（UTC `0 0 * * *`）を標準とし、10:00・12:00 JST/KSTを補完scheduleとする。`main` pushは外部APIを呼び出さず当日の試行権も消費せず、現在の公開dataを復元した`preserve` artifactを検証・配布し、予約実行だけが標準`live` modeを使う。日付別live-attempt markerをGitHub Actions cacheへ保存し、同じJST日付のmarkerがある場合は標準・補完live実行で外部収集と配布をskipする。markerは依存導入と全検証の完了後に生成し、cache永続化が成功した後だけ`publish-live`を開始する。cache保存に失敗するかmarkerが存在しない場合は外部収集を開始しない。これにより外部呼出段階前の失敗だけを補完し、外部呼出試行権を永続化した実行は成功・失敗・runner中断に関係なく自動再呼出しない。利用者判断による手動`force_live_retry=true`だけを重複防止の例外として許可する。workflow concurrencyで同時実行を防ぎ、予約遅延・公開repositoryの長期非activityによる停止可能性を運用点検へ含める。後続VPS/EC2では同じpipeline entryをsystemd timerの`Persistent=true`とOS file lockで実行する。

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

keyword分析器・stopword・LLM変更時はSchema 100%、入力外article ID・根拠・候補0件、国間混在0件、TOP 5重複0件、順位決定性100%、処理成功率80%以上を要求する。国別100件以上のfixtureで文断片除外、一般語除外、短い複合名詞保持、候補別最低3件・2媒体、関連記事接続精度を検証し、labelは国別最大5件のsampleで80%以上が受容可能であること。

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
  → 静的Web + data/v2 JSON artifact
  → GitHub Pages HTTPS

後続運用
Internet → nginx/ALB → FastAPI/uvicorn
VPS/EC2 systemdまたはcontainer scheduler → 同じbatch entry
```

- 初回Pages配布は公式Pages artifact方式で行い、生成JSONを`main`へ自動commitしない。
- PRはmock・fixtureだけで検証し、実ニュース・LLM Secretは保護された予約/手動運用workflowだけで利用する。
- 生成またはSchema検証に失敗した場合は既存Pages配布を維持し、失敗artifactを公開しない。
- 公式`actions/deploy-pages@v4`の内部待機上限である10分に合わせ、deploy jobも最大10分に制限する。`deployment_queued`状態で上限に達した場合は既存の正常なPages配布を維持し、GitHub Pagesの状態と実行logを確認して時間を置いた後、手動で一度だけ再試行する。同一commitの即時重複実行や代替配布方式への切替は行わない。
- Pages artifactには直近7日の公開可能JSON、静的Web、policy pageだけを含める。
- live buildは管理者用の選択記事と診断artifactを7日保持する。公開PagesとGitへ含めず、生成失敗時も可能な診断fileをuploadする。
- GitHub ActionsはNode.js 24互換majorの`actions/cache@v6`、`astral-sh/setup-uv@v9`、`actions/upload-artifact@v7`、`actions/upload-pages-artifact@v5`、`actions/deploy-pages@v5`を使用する。公開smokeは`dates.json`に列挙されたすべての日付JSONを取得し、直近7日artifact契約を検証する。
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
| Pages配布artifact `data/v2/` | 公開keyword resultと関連記事metadata | CI一時workspace | GitHub Pages | 公開可能fieldのみ、Secret・本文・raw log禁止 |
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
| 運用ニュースソース | GDELT・NAVER・NewsData.io無料枠と許可済み公式RSS/APIだけを使用し、NAVER日300回・月9,000回およびNewsData.io日40回・月1,200回hard stop、有料自動移行は禁止 |
| LLM | 初回運用は`mock`またはlocal code分析だけで0円、外部有料LLMは別途承認まで無効 |
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

### 方針変更後の追加実装日程 — keyword news v2

既存3週日程と完了履歴はbaselineとして維持し、次の3 PRを順番に進める。各PRは前PRのRebase and mergeとmerge後検証が終わった最新`main`から開始する。

| 順序 | branch・PR単位 | 実装内容 | 完了基準 |
|---|---|---|---|
| 1 | `codex/v2-gdelt-collection` | GDELT・NAVER adapter、国別query config、100件以上fixture、150/250収集・偏重・NAVER利用量停止基準 | mock・fixture標準CI、制限付きliveで国別100件以上または理由付きpartial |
| 2 | `codex/v2-keyword-pipeline` | 言語別名詞・複合名詞、stopword、同義語統合、決定的TOP 5、関連記事接続 | 国別100件fixtureで一般語除外・複合名詞・根拠・順位regression通過 |
| 3 | `codex/v2-schema-pages-ui` | Schema/API/data v2、DataSource migration、keyword詳細・関連記事最大20件、Pages artifact | v1維持、v2 producer/client同時移行、UI・全体・Pages smoke test通過 |
| 4 | `codex/v1-release-hardening` | 公開URL自動smoke、運用Runbook、7日batch観察、README・Release準備 | 現在の公開Pages検証、障害対応手順と7日観察証跡、全回帰通過 |
| 5 | `codex/v2-source-coverage` | source別収集量計測、国別無料経済news source・query補完、重複・偏重損失分析 | Secretなしfixture regression、無料上限順守、国別100件目標またはsource別根拠付きpartial |

2026-08-07時点で順序1のGDELT・NAVER adapter、versioned query、国別120件GDELT fixture、250件上限・媒体20%/30件制限、NAVER承認domainと日300回・月9,000回停止ledgerを実装した。制限付きGDELT live検証は無料endpointの429と媒体coverageにより国別100件未満となったため理由付きpartialとして記録し、v1予約実行では`--enable-gdelt`・`--enable-naver`明示前に有効化しない。

2026-08-08時点の順序2では、外部呼出し不要の言語別決定的候補抽出、国別stopword、入力候補限定の同義語統合、document frequency・媒体多様性・最新時刻・IDによるTOP 5と関連記事最大20件を実装する。国別120件fixtureで一般語除外、複合名詞保持、国分離、根拠接続、入力順序に依存しない順位を完了基準として検証する。

2026-08-08の実sampleでtitle先頭3語が文断片として表示される限界を確認し、韓国語`kiwipiepy`・日本語`SudachiPy`の形態素分析と英語単語正規化へ置き換える。候補は一単語または最大2形態素の短い複合名詞に制限し、最低3記事・2媒体を満たさない候補はTOP 5から除外する。

2026-08-08時点の順序3では既存v1を維持したままSchema 2.0、`/api/v2/keywords`、`data/v2`、独立JSON Repository、静的publisherを追加し、Web標準DataSourceをv2へ移行する。main pushは外部呼出し不要の国別120件fixture TOP 5を配布する。予約`publish-keyword-live`は直前24時間のGDELT・承認RSS・韓国NAVERを使い、3か国すべてが70件・TOP 5基準を満たす場合だけ新artifactを生成し、失敗時は最後の正常Pagesを維持する。NAVER Secretは`pages-production` Environmentだけで注入する。

順序4では配布結果に関係なく現在の公開URLのHTML・Schema 2.0・TOP5契約をretry付きで確認する`public-smoke` jobを追加する。運用Runbookと日付別観察表へ予約実行・手動retry・既存Pages維持結果を記録し、異なるJST日付7日分の証跡が揃った後だけ連続運用gateを完了する。

初回全経路確認用の過去収集は既存`publish-keyword-live`のJST日付別24時間計算を使い、過去保持が不確実なRSSと長時間HTTP retryを手動option`--skip-rss --single-attempt`だけで除外する。このoptionは予約workflowへ適用しない。2026-08-02～08のGDELT・NAVER遡及確認は全日が3か国100件基準未満で、公開fileを生成せず既存Pagesを維持した。この結果は機能動作確認であり、7日連続予約運用証跡には数えない。

順序5では無料source補完の前に、国・source別のraw受信件数、source別採用媒体分布、重複除去後件数、偏重制限後の最終件数を計測する。診断Schema 1.1には記事title・URL・ID・Secretを含めず集計値だけを記録する。NAVERの日300回・月9,000回と有料自動移行禁止を維持し、source・query変更は許可domainと利用条件を確認した項目だけ適用する。

2026-08-08の限定実接続ではNAVER 5 queryの500件中、既存許可domain 42件を確認した。上位除外domainをlocal診断で検討し、出所が明確な総合・経済専門媒体だけを許可listへ追加した`2026-08-08.v3`で103件を確保した。診断用の別ledgerは25/300回で、有料呼出しは使用していない。同じ実行でGDELT 3か国requestは`FeedFetchError`となったため、GDELT安定化と米国・日本の24時間coverageは引き続きpartialとして管理する。

GDELTの最小1件公開requestでもHTTP 429を再現した。HTTP errorは本文・URL・Secretなしで`rate_limited`、`client_error`、`server_error`、`timeout`などに分類し、一つの国で429が発生した場合は同じbatchの残りGDELT requestを`circuit_open_rate_limited`として即時停止する。RSSとNAVERは独立して継続する。

2026-08-08に米国・日本の補完sourceとしてNewsData.io無料Latest News APIを採用した。`NEWSDATA_API_KEY`はlocal `.env`と`pages-production` Environment Secretだけから注入し、US `country=us&language=en`・JP `country=jp&language=ja`へ`category=business`をそれぞれ適用する。mock pagination・response検証と日40回・月1,200回ledgerを実装し、直近24時間の限定実接続でUS・JP各100件を確保した。

2026-08-09の予約実行では重複・偏重除去後にUS 198件・JP 103件・KR 85件を確保したが、従来の100件gateにより全体配布が停止した。100件以上の推奨収集目標と150件の目標値は維持し、実配布下限だけを国別70件へ下げる。3か国すべてが70件以上で各国TOP 5を完成した場合のみ配布し、未達時は既存の正常Pagesを維持する。

配布障害対応は上記機能PRへ混在させない。GDELT利用条件・query偏り・形態素分析library選定が実装中に変わる場合はADRを更新する。

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
v0.9.1 keyword news v2設計確定
v0.10.0 GDELT大量収集と100件以上fixture
v0.11.0 言語別keyword TOP 5 pipeline
v0.12.0 Schema v2と関連記事Web移行
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
- [x] 公開Web URLで主要画面とAPIが動作
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
- [x] 運用Runbookと障害レポート例
- [x] プライバシーポリシーと問い合わせページ
- [ ] Android再開時にGoogle Play登録資料
- [ ] README、デモ画像、GitHub Release
- [ ] 開発日ごとの韓国語・日本語併記日次report

---

## 22. 最終定義

> 国別イシュークラウドは、米国・日本・韓国の経済ニュースを国別に独立収集し、LLMで各国内の類似した記事表現をイシュー単位へまとめ、ユニーク記事数と媒体多様性に基づく国別TOP 5をURLで表示するresponsive Web serviceである。結果には実際の出典とサンプル数を提示し、batch失敗、cache復旧、外部API費用などの運用課題を明示的に処理する。Androidアプリは公開Web安定化後に選択的に再開できるよう、API契約と設計記録を保全する。
