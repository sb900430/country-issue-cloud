# Repository working rules

## Bilingual specification

- `PROJECT_SPEC.md` is the Korean specification.
- `PROJECT_SPEC_JA.md` is the Japanese specification.
- Treat both files as equivalent sources of truth.
- When a requirement, architecture decision, schedule, policy, UI rule, or development convention changes, update both files in the same task and include both in the same commit.
- Before committing a specification change, check that section structure, numbers, dates, API paths, code examples, and decision status match across both files.

## Code comments

- Write method/function-level comments, KDoc, docstrings, and explanatory TODO/FIXME text only in Japanese.
- This applies to Kotlin, Python, JavaScript, and any source language added later.
- Do not add comments to self-explanatory methods merely to satisfy the rule.
- Identifiers, API names, library names, protocol terms, and official error messages may remain in their original language.

## Commit boundary

- Update the Korean and Japanese specifications together in one commit.
- Follow the milestone commit policy defined in both specification files.
- Start every commit subject with the actual commit date in `YYYY/MM/DD` format.
- Use `YYYY/MM/DD <type>: <English> | <한국어> | <日本語>`.
- Keep all three summaries concise and semantically equivalent. Example: `2026/08/03 feat: scaffold local environment | 로컬 환경 구성 | ローカル環境を構成`.

## Branch and pull request workflow

- Do not develop milestone changes directly on `main`.
- At the start of each milestone, update `main` and create the milestone branch defined in both specification files.
- Develop, test, and document the complete milestone on that branch.
- Squash temporary WIP commits into the milestone commit before publication.
- Push the milestone branch and open a Draft PR targeting `main`.
- Move the PR to ready only after `scripts/verify-all.ps1`, CI, and review pass.
- Merge through the PR. Do not push milestone or review-fix commits directly to `main`.
- After merge, switch to the updated `main` and run `scripts/verify-all.ps1` plus the available local smoke tests again against the merged code.
- A milestone is complete only after the post-merge checks on `main` pass.
- If a post-merge check fails, create `codex/post-merge-fix-<milestone>` from the failing `main`, fix it, and use another PR. Do not repair `main` directly.
- Delete the milestone branch only after post-merge verification passes, then start the next milestone from the verified `main`.

## AI development workflow

- Read `docs/AI_DEVELOPMENT_GUIDE.md` or `docs/AI_DEVELOPMENT_GUIDE_JA.md` before implementation work.
- Read and update both `docs/DEVELOPMENT_STATUS.md` and `docs/DEVELOPMENT_STATUS_JA.md` when a milestone starts or completes.
- Use Retrofit for Android HTTP and uv for Python dependency management unless an approved ADR changes the decision.
- Run `scripts/verify-all.ps1` before a milestone commit.
- A milestone is complete only when its implementation, tests, documentation, and verification pass together.
- Real news APIs and LLMs must not be called from the default test suite; use mocks and fixtures.
- Do not automatically approve visual regression baseline changes.
