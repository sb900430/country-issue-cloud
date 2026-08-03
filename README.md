# 국가별 이슈 클라우드 / 国別イシュークラウド

미국·일본·한국의 경제뉴스를 국가별로 독립 분석하여 그날의 주요 이슈 TOP 5를 보여주는 Android 및 웹 프로젝트입니다.

米国・日本・韓国の経済ニュースを国別に独立分析し、その日の主要イシューTOP 5を表示するAndroid・Webプロジェクトです。

## Repository layout

- `backend/`: FastAPI, batch processing, and local JSON repository
- `android/`: Kotlin and Jetpack Compose application
- `frontend/`: static web demonstration client
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

## Documentation

- Korean specification: `PROJECT_SPEC.md`
- Japanese specification: `PROJECT_SPEC_JA.md`
- AI development guide: `docs/AI_DEVELOPMENT_GUIDE.md`
- Current status: `docs/DEVELOPMENT_STATUS.md`

## Security

Do not commit API keys, client secrets, signing files, credentials, raw logs, or personal information. See `SECURITY.md` and run `scripts/check-secrets.ps1` before publishing changes.
