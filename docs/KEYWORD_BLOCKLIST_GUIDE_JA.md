# 国別禁止keyword管理ガイド

## 目的

運用結果で政治家名・政党名など経済イシューTOP 5に適さない表現を発見した場合、`config/keyword-blocklist.yml`へ国別規則として追加する。code定数を変更せずlistを段階的に拡張でき、すべての変更をGit履歴に残せる。

## 規則形式

```yaml
countries:
  KR:
    - term: "오세훈"
      match: "contains"
      category: "politics"
      reason_ko: "정치인 이름으로 경제 이슈 키워드에서 제외"
      reason_ja: "政治家名のため経済issue keywordから除外"
      added_on: "2026-08-11"
      enabled: true
```

- `term`：遮断する原文表現。2文字以上が必要。
- `match: exact`：候補全体が`term`と一致する場合だけ除外する。通常はこちらを優先する。
- `match: contains`：候補内に`term`を含む場合に除外する。人名・政党略称の結合形も遮断する必要がある場合だけ使う。
- `category`：`politics`、`person`、`template`、`noise`など除外種別を記録する。
- `reason_ko`、`reason_ja`：韓国語・日本語で同じ除外根拠を記録する。
- `added_on`：JST基準の追加日。
- `enabled`：`false`の場合、履歴は維持するがfilterを適用しない。

## 追加手順

1. 非公開の管理者向けActions artifactにある`selected-articles.json`と実際のTOP 5を確認する。
2. 複数記事で反復するが、本projectの経済イシュー目的と無関係な表現か確認する。
3. 対象国のlistへ規則を追加し、誤検知riskが低い`exact`を先に使う。
4. 韓国語・日本語の理由と追加日を記録する。
5. keyword regression testと`scripts/verify-all.ps1`を実行する。
6. PRで根拠と影響範囲を確認してからmergeする。

設定fileがない場合、Schema不正、または同一国内に同じ規則が重複した場合はbatchを失敗させる。この場合、既存の正常Pages結果は維持される。運用中に直ちに戻す必要がある場合は規則を削除せず、`enabled: false`へ変更して履歴を保つ。
