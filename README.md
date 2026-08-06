# 국가별 이슈 클라우드 / 国別イシュークラウド

미국·일본·한국의 경제뉴스를 국가별로 독립 분석하여 그날의 주요 이슈 TOP 5를 URL로 보여주는 반응형 웹 프로젝트입니다. Android 앱은 공개 웹 안정화 이후 선택적으로 재개할 수 있도록 보류합니다.

1차 운영은 GitHub Actions가 정적 JSON을 생성하고 GitHub Pages가 웹과 데이터를 제공하는 방식입니다. FastAPI와 동일 Schema의 API adapter를 유지하여 향후 VPS/EC2로 전환할 때 UI 로직을 바꾸지 않습니다.

米国・日本・韓国の経済ニュースを国別に独立分析し、その日の主要イシューTOP 5をURLで表示するresponsive Webプロジェクトです。Androidアプリは公開Web安定化後に選択的に再開できる保留trackです。

初回運用はGitHub Actionsが静的JSONを生成し、GitHub PagesがWebとdataを提供する。FastAPIと同じSchemaのAPI adapterを維持し、将来VPS/EC2へ移行してもUI logicを変更しない。

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

The default mode is `fixture`; real news APIs and LLMs are not called by the default test suite. Copy `backend/.env.example` to the ignored `backend/.env` only when local environment values are needed.

Build and preview a fixture-backed Pages artifact:

```powershell
.\scripts\build-pages-site.ps1 -Mode fixture -OutputDirectory .\preview-site
Set-Location .\preview-site
python -m http.server 8080
```

`publish-live` reads only approved, enabled official feeds from `config/sources.example.yml`. The scheduled Pages workflow runs every day at 07:00 UTC (16:00 JST/KST), validates the public artifact, and deploys only after successful generation. A failed build does not replace the last successful Pages deployment.

## Documentation

- Korean specification: `PROJECT_SPEC.md`
- Japanese specification: `PROJECT_SPEC_JA.md`
- AI development guide: `docs/AI_DEVELOPMENT_GUIDE.md`
- Current status: `docs/DEVELOPMENT_STATUS.md`
- Conditional API registration: `docs/SOURCE_REGISTRATION_GUIDE.md`

## Security

Do not commit API keys, client secrets, signing files, credentials, raw logs, or personal information. See `SECURITY.md` and run `scripts/check-secrets.ps1` before publishing changes.
