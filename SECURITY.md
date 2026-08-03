# Security Policy

Do not open a public issue containing credentials or personal information. Report suspected credential exposure through GitHub's private vulnerability reporting when available.

If a secret is committed, revoke and rotate it immediately. Removing the value in a later commit is not sufficient because it remains in Git history.

The Android application must never contain news-provider keys, LLM keys, client secrets, database credentials, administrator tokens, signing passwords, or private keys.
