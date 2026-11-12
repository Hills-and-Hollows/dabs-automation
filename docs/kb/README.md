# Hills & Hollows DABS knowledge SoR

Grok Bot Pages are drafts; merged repo docs are canonical.

**Purpose:** single source of record for Hills & Hollows LLC Utah DABS **PA-539** package agency knowledge in this repo.

Agents must **cite live sources** from [SOURCES.md](SOURCES.md) and **never guess** license, order, cash, bond, or filing facts. If a fact is not Proven in the inventory receipt or a later live re-read, mark it **Unknown**.

This tree is a knowledge index only. It does **not** change licenses, orders, filings, or portal automation.

## BINDING — Shawn Approve t436u (hosting / domain)

Separate apps are OK **only** if they stay in sync as **one HH business** (ops, accounting, taxes, financial forecasting).

| Rule | Binding |
|---|---|
| Default host | Prefer **locally hosted Docker containers** for all apps |
| Railway (if used) | MUST be at `www.[APP_NAME].hillsandhollowsmarket.com` |
| Twin-consolidate EDG | Next EDG **must** include a domain plan under that hostname pattern |
| Peer boundary | Still **PEER_NOT_INTEGRATE** (t434s2287): do **not** fold into sscs-qbo-sync |
| Railway mutate | **No** mutate without a **new** Shawn Approve |

See [HANDOFFS.md](HANDOFFS.md) and [RAILWAY.md](RAILWAY.md). This PR does **not** attach domains or mutate Railway.

## BINDING — Shawn Approve t441u (continue-when-final)

Never wait on Shawn for testing, QA E2E, merging, or cleanup when work is **final** and creates **no new bugs**. Continue when ready; **report after**.

| Rule | Binding |
|---|---|
| Continue-when-final | Testing, QA E2E, merging, and cleanup may proceed when work is **final** and creates **no new bugs**; report after |
| Docs/kb + twin cleanup | Docs/kb merges and twin cleanup that is **proven-final** may proceed without pre-merge Approve; report after |
| Ask-first still | send / pay / sign / file / delete / license-order / Railway mutate that spends or exposes |
| Does **not** authorize | Railway mutate that spends/exposes, InstallPlugin, file/order/license, or pay/send/sign |

See [HANDOFFS.md](HANDOFFS.md), [RAILWAY.md](RAILWAY.md), and [SKILLS.md](SKILLS.md).

## Inventory and peer receipts

| Artifact | Primary receipt |
|---|---|
| Fleet #65 | https://github.com/ShawnOwen/fleet-board/issues/65 (receipt comment `#issuecomment-6583982494`) |
| Inventory (this SoR) | phase0 receipt `2026-11-02T10:55:00-07:00`; SoR layout #46 (`73c18365`); deepen #47 (`dad15b2`) receipt `2026-11-02T10:48:00-07:00` |
| Peer ops #64 (cash SoR) | unverified – Page draft only (settlement amounts in this repo cite `gmail-mercury-abc-finet`) |

Phase0 receipt: `2026-11-02T10:55:00-07:00`. Deepen receipt: `2026-11-02T10:48:00-07:00`. Live Drive re-read: `2026-11-02` (scorecard + bond tracker + Travelers PDF metadata). Statuses in [SOURCES.md](SOURCES.md) stay Proven / Stale / Missing / **Proven-candidate** — do not invent new labels.

## Handoffs (do not execute here)

| Topic | Hand off to |
|---|---|
| Liquor / sales-tax | Tax Filings Catch-up |
| CDBWin / QBO day books | sscs-qbo-sync + Omachi (**PEER_NOT_INTEGRATE:** DABS Railway stays a peer — do not fold into sscs-qbo-sync; Shawn Approve t434s2287) |
| Settlement cash SoR | Peer ops #64 (this repo is **not** cash SoR) |
| Cash-flow context | HH Cash Flow |

See [HANDOFFS.md](HANDOFFS.md).

## Ask-first (hard stop)

Hard-stop: do **not** send, pay, sign, file, delete, license-order, or Railway-mutate that spends or exposes without an explicit Shawn Approve.

Docs/kb merges may proceed when work is **final** and creates **no new bugs** (t441u); report after. This PR is docs only.

t441u does **not** authorize Railway mutate that spends/exposes, InstallPlugin, file/order/license, or pay/send/sign.

## Confluence — Missing / Blocked

**Status: Missing / Blocked.** Atlassian connector is not installed yet. Connector install = **separate Approve only** (no InstallPlugin from this PR). Do **not** invent Confluence URLs or treat wiki pages as Proven.

## Drive deepen (2026-11-02)

Live Google Drive read of the Proven scorecard and Stale bond tracker is recorded in [SOURCES.md](SOURCES.md) / [FACTS.md](FACTS.md). A later Travelers PDF is **Proven-candidate** only — it may supersede tracker `issued=NO` for the $55,000 consignment instrument; do **not** claim DABS acceptance. Gap Tracker rows remain **Open** even when weekly Run Log `Open Gaps Count=0` — do not silently close.

## Layout

| File | Role |
|---|---|
| [SOURCES.md](SOURCES.md) | Proven / Stale / Missing / Proven-candidate index |
| [FACTS.md](FACTS.md) | Facts from Proven receipt + live deepen citations only |
| [SKILLS.md](SKILLS.md) | Intended skills (none exist yet); t441u docs-merge OK when final |
| [HANDOFFS.md](HANDOFFS.md) | Peer map + t436u BINDING + t441u |
| [RAILWAY.md](RAILWAY.md) | Peer Railway stub + t436u hostname (no deploy) + t441u |
| [SECURITY-ROTATE.md](SECURITY-ROTATE.md) | Credential rotate guidance |
