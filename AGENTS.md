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
