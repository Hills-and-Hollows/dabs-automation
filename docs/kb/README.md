# Hills & Hollows DABS knowledge SoR

**Purpose:** single source of record for Hills & Hollows LLC Utah DABS **PA-539** package agency knowledge in this repo.

Agents must **cite live sources** from [SOURCES.md](SOURCES.md) and **never guess** license, order, cash, bond, or filing facts. If a fact is not Proven in the inventory receipt, mark it **Unknown**.

This tree is a knowledge index only. It does **not** change licenses, orders, filings, or portal automation.

## Inventory and peer Pages

| Artifact | URL |
|---|---|
| Fleet #65 | https://github.com/ShawnOwen/fleet-board/issues/65 |
| Inventory Page (this SoR receipt) | https://cursor.com/canvas/store-a64ca9c3-bb59-4536-9469-209a5d979449/2bcfdf4f-54b8-4d7f-96fc-9441a886051e |
| Peer ops Page #64 | https://cursor.com/canvas/store-a64ca9c3-bb59-4536-9469-209a5d979449/66ccb63a-3928-4439-839c-94c9170a454c |

Receipt timestamp: `2026-11-02T10:55:00-07:00` (phase0 inventory JSON). Statuses in [SOURCES.md](SOURCES.md) are copied from that receipt — do not invent new Proven/Stale/Missing labels.

## Handoffs (do not execute here)

| Topic | Hand off to |
|---|---|
| Liquor / sales-tax | Tax Filings Catch-up |
| CDBWin / QBO day books | sscs-qbo-sync + Omachi (**PEER_NOT_INTEGRATE:** DABS Railway stays a peer — do not fold into sscs-qbo-sync; Shawn Approve t434s2287) |
| Settlement cash SoR | Peer ops #64 (this repo is **not** cash SoR) |
| Cash-flow context | HH Cash Flow |

See [HANDOFFS.md](HANDOFFS.md).

## Ask-first (hard stop)

Do **not** file, order, license, pay, send, sign, or merge without an explicit Shawn Approve. This PR is docs + credential-file hygiene only.

## Confluence — Missing / Blocked

**Status: Missing / Blocked.** Atlassian connector is not installed yet. Connector install = **separate Approve only** (no InstallPlugin from this PR). Do **not** invent Confluence URLs or treat wiki pages as Proven.

## Drive deepen (in progress)

Drive Proven/Stale/Missing labels stay exactly as copied from the inventory JSON. Drive deepen continues on the **HH DABS Expert** side. [SOURCES.md](SOURCES.md) will be amended in a **follow-up commit** if the live Drive read changes a citation. Do not guess Drive contents here.

## Layout

| File | Role |
|---|---|
| [SOURCES.md](SOURCES.md) | Proven / Stale / Missing index |
| [FACTS.md](FACTS.md) | Stub facts from Proven receipt only |
| [SKILLS.md](SKILLS.md) | Intended skills (none exist yet) |
| [HANDOFFS.md](HANDOFFS.md) | Peer map |
| [RAILWAY.md](RAILWAY.md) | Known Railway project names (no deploy) |
| [SECURITY-ROTATE.md](SECURITY-ROTATE.md) | Credential rotate guidance |
