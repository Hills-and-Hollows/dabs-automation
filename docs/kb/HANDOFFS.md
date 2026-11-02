# Peer handoffs

This repo indexes PA-539 knowledge. It does not own tax filings, day-book sync, or cash forecast. Ask-first still: send / pay / sign / file / delete / license-order / Railway mutate that spends or exposes. Docs/kb merges that are **final** and create **no new bugs** may proceed under t441u; report after.

## BINDING — Shawn Approve t436u (hosting / domain)

- Separate apps are OK **only** if they stay in sync as **one HH business** (ops, accounting, taxes, financial forecasting).
- Prefer **locally hosted Docker containers** for all apps.
- If an app is deployed to Railway, it **MUST** be hosted at `www.[APP_NAME].hillsandhollowsmarket.com`.
- The next twin-consolidate EDG **must** include a domain plan under that hostname pattern.
- This is a peer note only. Do **not** attach domains or mutate Railway from this PR.

## PEER — t441u (twin cleanup)

Twin cleanup that is **proven-final** may proceed under t441u without pre-merge Approve; report after. Still **no** Railway mutate that spends or exposes without Approve. Next twin-consolidate EDG still needs the t436u domain plan (`www.[APP_NAME].hillsandhollowsmarket.com`).

## PEER_NOT_INTEGRATE (Shawn Approve t434s2287)

DABS Railway stays a **peer** app — do **not** fold it into sscs-qbo-sync. Twin consolidate (Balancing Rock `dabs-automation` ghost vs Hills Hollows DABS Backend) and Atlassian/Confluence connector = **separate Approves only**; no Railway mutate without a **new** Approve; no InstallPlugin from this PR. Live receipt (conceptual): three Balancing Rock projects + offline knowledge-base shell; Backend has vars/no domain; ghost has neither; Single Source Chat DABS last deploy FAILED. See [RAILWAY.md](RAILWAY.md).

| Peer | Role | Notes |
|---|---|---|
| Fleet #64 ops Page | Peer operations SoR | https://cursor.com/canvas/store-a64ca9c3-bb59-4536-9469-209a5d979449/66ccb63a-3928-4439-839c-94c9170a454c — settlement cash SoR lives here, not in this repo |
| Tax Filings Catch-up | Liquor / sales-tax filings | Hand off; do not file from this tree |
| sscs-qbo-sync | CDBWin / QBO day books | Hand off with Omachi. Peer only — **not** a Railway merge target. Stay in sync as one HH business (t436u); do not fold DABS into this repo |
| Omachi | CDBWin / QBO day-book companion | Hand off with sscs-qbo-sync |
| HH Cash Flow | Cash-flow / forecast context | Peer FYI only; not a license or order authority |
| DABS Railway | Peer app (Balancing Rock trio + offline KB shell) | **PEER_NOT_INTEGRATE**. If Railway is used: `www.[APP_NAME].hillsandhollowsmarket.com` (t436u). Prefer local Docker. No mutate without new Approve |

Fleet inventory for this SoR: [#65](https://github.com/ShawnOwen/fleet-board/issues/65).
