# 국가별 이슈 클라우드 / 国別イシュークラウド

미국·일본·한국 언론사의 경제뉴스를 국가별 150건 목표로 독립 수집하고, 반복 출현하는 명사·복합명사를 국가별 키워드 TOP 5로 보여주는 반응형 웹 프로젝트입니다. 키워드를 누르면 해당 키워드의 관련 기사를 확인할 수 있습니다. Android 앱은 공개 웹 안정화 이후 선택적으로 재개할 수 있도록 보류합니다.

1차 운영은 GitHub Actions가 정적 JSON을 생성하고 GitHub Pages가 웹과 데이터를 제공하는 방식입니다. FastAPI와 동일 Schema의 API adapter를 유지하여 향후 VPS/EC2로 전환할 때 UI 로직을 바꾸지 않습니다.

米国・日本・韓国の報道機関の経済ニュースを国別150件目標で独立収集し、反復出現する名詞・複合名詞を国別keyword TOP 5として表示するresponsive Webプロジェクトです。keywordから関連記事を確認できます。Androidアプリは公開Web安定化後に選択的に再開できる保留trackです。

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

The default mode is `fixture`; real news APIs and LLMs are not called by the default test suite. Copy `backend/.env.example` to the ignored `backend/.env` only when local environment values are needed. Follow `docs/SOURCE_REGISTRATION_GUIDE.md` for the free-source variable matrix and NAVER registration procedure.

Build and preview a fixture-backed Pages artifact:

```powershell
.\scripts\build-pages-site.ps1 -Mode fixture -OutputDirectory .\preview-site
Set-Location .\preview-site
python -m http.server 8080
```

The GDELT DOC API and NAVER API HUB collectors, versioned queries, 250-article cap, publisher allowlists, and NAVER usage hard stops are implemented. To preserve the existing v1 contract, scheduled `publish-live` still uses RSS only; GDELT and NAVER are enabled explicitly with `--enable-gdelt` and `--enable-naver` during bounded evaluation and will become defaults when the v2 producer and client migrate together. A push to `main` builds and deploys the fixture artifact without calling external sources. The Pages workflow attempts live publishing at 00:00 UTC (09:00 JST/KST), with 10:00 and 12:00 JST/KST catch-up schedules. A date-keyed attempt marker prevents any automatic second external collection after the live stage has been claimed; only an explicit manual `force_live_retry` can override it.

## Documentation

- Korean specification: `PROJECT_SPEC.md`
- Japanese specification: `PROJECT_SPEC_JA.md`
- AI development guide: `docs/AI_DEVELOPMENT_GUIDE.md`
- Current status: `docs/DEVELOPMENT_STATUS.md`
- Free API environment and registration guide: `docs/SOURCE_REGISTRATION_GUIDE.md`
- Keyword-news redesign decision: `docs/adr/ADR-0001-keyword-news-pipeline.md`

## Security

Do not commit API keys, client secrets, signing files, credentials, raw logs, or personal information. See `SECURITY.md` and run `scripts/check-secrets.ps1` before publishing changes.
