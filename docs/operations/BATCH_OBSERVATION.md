# Batch Observation / 배치 관찰 / バッチ観察

민감정보와 원문 로그를 기록하지 않는다. / Secretとraw logを記録しない。

| JST date | Scheduled run | Result | Published data date | US / JP / KR articles | Existing Pages preserved | Note |
|---|---|---|---|---|---|---|
| 2026-08-08 | Not applicable — v2 merged after 09:00 | Fixture deploy verified | 2026-08-07 | 120 / 120 / 120 | Yes | Public UI, TOP5, layout switch and 20 related links passed |
| 2026-08-10 | 09:00 scheduled run | Published, quality review failed | 2026-08-10 | 139 / 117 / 72 | No — new live data published | Repetitive template terms, date/unit fragments and overlapping related-article sets found; GDELT returned 429 and is temporarily disabled by the follow-up fix |

## Initial historical pipeline check / 초기 소급 동작 확인 / 初回遡及動作確認

운영 연속 실행 증거와 분리한 수동 점검이다. GDELT와 NAVER를 사용하고 과거 보존이 불확실한 RSS는 제외했으며 HTTP 요청은 날짜별 단일 시도로 제한했다. / 運用連続実行の証跡とは分離した手動確認である。GDELTとNAVERを使い、過去保持が不確実なRSSを除外し、HTTP requestは日付別単一試行に制限した。

| Target date | Result | US / JP / KR articles | Published | Note |
|---|---|---|---|---|
| 2026-08-02 | FAILED | 0 / 0 / 0 | No | Three-country 100-article gate preserved |
| 2026-08-03 | FAILED | 34 / 0 / 90 | No | Partial source coverage only |
| 2026-08-04 | FAILED | 0 / 0 / 0 | No | No valid country reached the threshold |
| 2026-08-05 | FAILED | 0 / 26 / 90 | No | Partial source coverage only |
| 2026-08-06 | FAILED | 0 / 0 / 0 | No | No valid country reached the threshold |
| 2026-08-07 | FAILED | 0 / 0 / 0 | No | No valid country reached the threshold |
| 2026-08-08 | FAILED | 0 / 0 / 37 | No | Current-day partial window |

- NAVER local ledger after all attempts: daily 40 / 300, monthly 40 / 9,000.
- No `keyword-published` output was created and the public Pages deployment was not modified.
- This table does not satisfy the seven-distinct-day scheduled operation gate.

완료 기준 / 完了基準: 서로 다른 JST 날짜 7일 기록 / 異なるJST日付7日分を記録
