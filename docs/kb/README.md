# Hills & Hollows DABS knowledge SoR

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

## Inventory and peer Pages

| Artifact | URL |
|---|---|
| Fleet #65 | https://github.com/ShawnOwen/fleet-board/issues/65 |
| Inventory Page (this SoR receipt) | https://cursor.com/canvas/store-a64ca9c3-bb59-4536-9469-209a5d979449/2bcfdf4f-54b8-4d7f-96fc-9441a886051e |
| Peer ops Page #64 | https://cursor.com/canvas/store-a64ca9c3-bb59-4536-9469-209a5d979449/66ccb63a-3928-4439-839c-94c9170a454c |

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

Do **not** file, order, license, pay, send, sign, or merge without an explicit Shawn Approve. This PR is docs only.

## Confluence — Missing / Blocked

**Status: Missing / Blocked.** Atlassian connector is not installed yet. Connector install = **separate Approve only** (no InstallPlugin from this PR). Do **not** invent Confluence URLs or treat wiki pages as Proven.

## Drive deepen (2026-11-02)

Live Google Drive read of the Proven scorecard and Stale bond tracker is recorded in [SOURCES.md](SOURCES.md) / [FACTS.md](FACTS.md). A later Travelers PDF is **Proven-candidate** only — it may supersede tracker `issued=NO` for the $55,000 consignment instrument; do **not** claim DABS acceptance. Gap Tracker rows remain **Open** even when weekly Run Log `Open Gaps Count=0` — do not silently close.

## Layout

| File | Role |
|---|---|
| [SOURCES.md](SOURCES.md) | Proven / Stale / Missing / Proven-candidate index |
| [FACTS.md](FACTS.md) | Facts from Proven receipt + live deepen citations only |
| [SKILLS.md](SKILLS.md) | Intended skills (none exist yet) |
| [HANDOFFS.md](HANDOFFS.md) | Peer map + t436u BINDING |
| [RAILWAY.md](RAILWAY.md) | Peer Railway stub + t436u hostname (no deploy) |
| [SECURITY-ROTATE.md](SECURITY-ROTATE.md) | Credential rotate guidance |
