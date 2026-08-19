# 국가별 이슈 클라우드 / 国別イシュークラウド

미국·일본·한국 언론사의 경제뉴스를 국가별 150건 목표로 독립 수집하고, 품질 기준을 통과한 반복 명사·복합명사를 국가별 최대 5개로 보여주는 반응형 웹 프로젝트입니다. 키워드를 누르면 해당 키워드의 관련 기사를 확인할 수 있습니다. Android 앱은 공개 웹 안정화 이후 선택적으로 재개할 수 있도록 보류합니다.

1차 운영은 GitHub Actions가 정적 JSON을 생성하고 GitHub Pages가 웹과 데이터를 제공하는 방식입니다. FastAPI와 동일 Schema의 API adapter를 유지하여 향후 VPS/EC2로 전환할 때 UI 로직을 바꾸지 않습니다.

米国・日本・韓国の報道機関の経済ニュースを国別150件目標で独立収集し、品質基準を通過した反復名詞・複合名詞を国別最大5件表示するresponsive Webプロジェクトです。keywordから関連記事を確認できます。Androidアプリは公開Web安定化後に選択的に再開できる保留trackです。

初回運用はGitHub Actionsが静的JSONを生成し、GitHub PagesがWebとdataを提供する。FastAPIと同じSchemaのAPI adapterを維持し、将来VPS/EC2へ移行してもUI logicを変更しない。

## Live demo

- Public site / 공개 사이트 / 公開site: https://kimsb0430.github.io/country-issue-cloud/
- Default view: Korea quality-keyword tiles; switch countries or enable cloud view
- Keyword detail: up to 20 related source links
- Data contract: `data/v2/latest.json`, `calendar.json`, `status.json`, and up to seven attempt dates

The public URL is checked after every Pages workflow by `scripts/check-public-site.ps1`. The check validates HTTPS, primary UI markers, Schema 2.0, all three countries, publication status, and three to five keywords for each successful country. 한 국가만 성공해도 해당 국가는 표시하고 실패 국가는 기사 수와 사유를 보여줍니다. 1か国だけ成功した場合も成功国を表示し、失敗国には記事数と理由を表示します。

## Repository layout

- `backend/`: FastAPI, batch processing, and local JSON repository
- `android/`: deferred Android application track; preserved for a later decision
- `frontend/`: responsive Pages client with static/API DataSource adapters
- `deploy/`: GitHub Pages workflow support and deferred VPS/EC2 templates
- `config/`: non-secret source and runtime configuration examples
- `sample-data/`: sanitized fixtures used without external API calls
- `scripts/`: unified local verification commands

## Local development

Install [uv](https://docs.astral.sh/uv/) and run:

```powershell
uv sync --project backend --locked --group dev
.\scripts\verify-all.ps1
```

The default mode is `fixture`; real news APIs and LLMs are not called by the default test suite. Copy `backend/.env.example` to the ignored `backend/.env` only when local environment values are needed. Follow `docs/SOURCE_REGISTRATION_GUIDE.md` for the free-source variable matrix and NAVER registration procedure.

Build and preview a fixture-backed Pages artifact:

```powershell
.\scripts\build-pages-site.ps1 -Mode fixture -OutputDirectory .\preview-site
Set-Location .\preview-site
python -m http.server 8080
```

The v2 Pages client reads `data/v2` keyword JSON. A push to `main` builds a network-free three-country 120-article fixture artifact with quality keywords and related articles. Scheduled runs collect a 24-hour source window through approved RSS, NewsData.io for the US and Japan, and NAVER for Korea. NewsData.io's free-tier window is shifted by its 12-hour delivery delay; NAVER uses a target-aware second page, and JPX/FSA RSS supplements Japanese publisher diversity. Successful countries are published independently, while `calendar.json` and `status.json` explain unavailable countries and failed dates. The workflow runs at 04:00 UTC (13:00 JST/KST), with 14:00 and 16:00 JST/KST catch-up candidates. A date-keyed marker is checked by the Ubuntu gate, persisted by the Windows build after verification, and shared with explicit cross-OS cache support before external collection; only an explicit manual `force_live_retry` can override it.

## Documentation

- Korean specification: `PROJECT_SPEC.md`
- Japanese specification: `PROJECT_SPEC_JA.md`
- AI development guide: `docs/AI_DEVELOPMENT_GUIDE.md`
- Current status: `docs/DEVELOPMENT_STATUS.md`
- Free API environment and registration guide: `docs/SOURCE_REGISTRATION_GUIDE.md`
- Keyword-news redesign decision: `docs/adr/ADR-0001-keyword-news-pipeline.md`
- Operations runbook: `docs/OPERATIONS_RUNBOOK.md`
- Seven-day batch observation: `docs/operations/BATCH_OBSERVATION.md`
- v1.0 release checklist: `docs/releases/V1_RELEASE_CHECKLIST.md`

## Security

Do not commit API keys, client secrets, signing files, credentials, raw logs, or personal information. See `SECURITY.md` and run `scripts/check-secrets.ps1` before publishing changes.
