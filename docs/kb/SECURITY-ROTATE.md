# Credential rotate guidance

## `.env.quickbooks` (this PR)

Assume credentials that were stored in the tracked root file `.env.quickbooks` **may have been exposed via git history**.

**Do now (owner, Intuit developer portal):**

1. Rotate QuickBooks app **client secret** and re-issue **OAuth tokens** (access + refresh) for the Hills & Hollows QBO app.
2. Store replacements only in a local untracked env file or a secret manager — never re-commit live secrets.
3. Use template files only: [`.env.quickbooks.example`](../../.env.quickbooks.example) / `.env.example`.

**Do later (separate Shawn Approve — not this PR):**

- History purge with BFG or `git filter-repo` for `.env.quickbooks`.
- Do **not** merge, file, order, license, pay, send, or sign as part of rotate.

This branch **untracks** `.env.quickbooks` and adds ignore rules. The blob may still exist on `main` history until the purge Approve.

## Follow-up flag (out of scope here)

Tracked `dabs_auth.json` (repo root) and `scripts/dabs_auth.json` were **not** untracked in this PR. Treat them as a later hygiene flag — do not dump contents.

## Never

- Re-commit live QuickBooks or DABS portal secrets.
- Paste secret values into PRs, issues, chat, or logs.
- Open or quote `.env.quickbooks` contents in documentation.
