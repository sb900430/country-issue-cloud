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
- Follow the weekly commit policy defined in both specification files.
- Start every commit subject with the actual commit date in `YYYY/MM/DD` format.
- Use `YYYY/MM/DD <type>: <English> | <한국어> | <日本語>`.
- Keep all three summaries concise and semantically equivalent. Example: `2026/08/03 feat: scaffold local environment | 로컬 환경 구성 | ローカル環境を構成`.

## Branch and pull request workflow

- Do not develop weekly changes directly on `main`.
- At the start of each development week, update `main` and create the weekly branch defined in both specification files.
- Develop, test, and document the complete weekly scope on that branch.
- Squash temporary WIP commits into the weekly commit before publication.
- Push the weekly branch and open one Draft PR targeting `main`.
- Move the PR to ready only after `scripts/verify-all.ps1`, CI, and review pass.
- Merge through the PR using **Rebase and merge** so the validated multilingual weekly commit subject is preserved and no automatic merge commit is added.
- Do not use **Create a merge commit**. Use **Squash and merge** only as an exception when WIP commits could not be squashed locally, and manually set the squash commit subject to the required multilingual format.
- Do not push weekly or review-fix commits directly to `main`.
- After merge, switch to the updated `main` and run `scripts/verify-all.ps1` plus the available local smoke tests again against the merged code.
- A development week is complete only after the post-merge checks on `main` pass.
- If a post-merge check fails, create `codex/post-merge-fix-week-<number>` from the failing `main`, fix it, and use another PR. Do not repair `main` directly.
- Delete the weekly branch only after post-merge verification passes, then start the next weekly branch from the verified `main`.

## AI development workflow

- Read `docs/AI_DEVELOPMENT_GUIDE.md` or `docs/AI_DEVELOPMENT_GUIDE_JA.md` before implementation work.
- Read and update both `docs/DEVELOPMENT_STATUS.md` and `docs/DEVELOPMENT_STATUS_JA.md` when a development week starts or completes.
- At the end of every day with development activity, create or update `docs/daily/YYYY-MM-DD.md` from `docs/daily/TEMPLATE.md`.
- Write each daily report as one Git-tracked Markdown file containing equivalent Korean and Japanese sections.
- Include the day's goal, completed work, important files, verification results, decisions, risks, and next task. Never include secrets or raw sensitive logs.
- Keep daily reports on the active weekly branch and include them in that week's final commit and PR; do not create separate daily commits.
- Use Retrofit for Android HTTP and uv for Python dependency management unless an approved ADR changes the decision.
- Run `scripts/verify-all.ps1` before a weekly commit.
- A development week is complete only when its implementation, tests, documentation, and verification pass together.
- Real news APIs and LLMs must not be called from the default test suite; use mocks and fixtures.
- Do not automatically approve visual regression baseline changes.

## Weekly review

- Follow `docs/review/WEEKLY_REVIEW_GUIDE.md` and use `docs/review/WEEKLY_REVIEW_TEMPLATE.md`.
- Trigger the review immediately when the active week's implementation, tests, documentation, and `scripts/verify-all.ps1` all pass; do not wait for a fixed weekday.
- Run at most one completed review for the same weekly candidate SHA unless that SHA changes after a Critical/High fix.
- Limit the review phase to 60 minutes. Retry only transient command failures once.
- Require changed-code line coverage of 80%; apply module thresholds defined in the guide.
- Allow at most two safe fix attempts per Critical/High finding and a separate 90-minute fix window.
- Store review reports only under ignored `reviews/`; do not commit them.
- Advance `reviews/.last-reviewed-sha` only after a complete review.
