# v1.0 Release Checklist / 출시 체크리스트 / リリースチェックリスト

## Release candidate

| Item | Status | Evidence |
|---|---|---|
| Schema 2.0 and v1 compatibility | PASS | backend and Web contract tests |
| Three-country fixture keywords | PASS | 120 articles per country, three to five quality keywords, related links |
| Public Pages primary flow | PASS | country/layout/detail browser smoke on 2026-08-08 |
| Automated public smoke | PASS | `scripts/check-public-site.ps1` and Pages `public-smoke` job |
| Secret protection | PASS | local scan and GitHub Secret protection |
| Operations runbook | PASS | `docs/OPERATIONS_RUNBOOK.md` |
| Seven distinct JST scheduled runs | PENDING | `docs/operations/BATCH_OBSERVATION.md` |
| Release tag and GitHub Release | PENDING | create only after seven-day gate |

## 한국어 공개 기준

- Critical/High 미해결 항목이 없어야 한다.
- 최신 `main`에서 전체 검증과 fixture Pages smoke가 통과해야 한다.
- 공개 URL에서 세 국가, 품질 키워드 3~5개, 부분 성공 상태, layout 전환, 상세 관련 기사 흐름이 동작해야 한다.
- 서로 다른 JST 날짜 7일의 예약 실행 결과와 기존 정상 Pages 보존 여부가 기록되어야 한다.
- 위 기준 전에는 `v1.0.0` tag와 GitHub Release를 만들지 않는다.

## 日本語公開基準

- Critical/High未解決項目がないこと。
- 最新`main`で全検証とfixture Pages smokeが通過すること。
- 公開URLで3か国、品質keyword 3～5件、部分成功状態、layout切替、詳細関連記事flowが動作すること。
- 異なるJST日付7日分の予約実行結果と既存正常Pages維持有無が記録されること。
- 上記基準を満たす前に`v1.0.0` tagとGitHub Releaseを作成しないこと。
