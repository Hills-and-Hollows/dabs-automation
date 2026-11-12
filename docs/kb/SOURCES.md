# Sources index

Copied from the phase0 inventory receipt (`2026-11-02T10:55:00-07:00`) for fleet [#65](https://github.com/ShawnOwen/fleet-board/issues/65), then amended by the 2026-11-02 Drive deepen (receipt `2026-11-02T10:48:00-07:00`; live Google Drive read of scorecard, bond tracker, and Travelers PDF metadata).

**Inventory receipt:** phase0 `2026-11-02T10:55:00-07:00`; frozen in docs/kb via #46 (`73c18365`); deepen receipt `2026-11-02T10:48:00-07:00` (receipt records #46; #47 / `dad15b2` is the squash that landed it).

Counts: Proven 5 / Stale 5 / Missing 5 / **Proven-candidate 1**. Do **not** invent new statuses. Do **not** invent official DABS rules (`official-dabs-rules` stays Missing).

## Proven

| ID | URL / path | Notes |
|---|---|---|
| `drive-compliance-scorecard` | https://docs.google.com/spreadsheets/d/1rt1CRoT0LX3EJnTbbIxvzJD5ydIEEY_ewkfeMtUMmXs | Live Drive read 2026-11-02. Sheet title: *DABS Compliance Scorecard - Log Tracker (Hills and Hollows LLC)*. Drive `modifiedTime` `2026-11-02T14:58:19Z`. Latest Run Log row: **RUN-2026-11-02-01** Result **PASS**, Total 100, FAIL 0, N/V 0, **Open Gaps Count=0**. Instructions tab names **Portal: Utah DABS OpenGov**. Gap Tracker still lists **Status=Open** for GAP-001–004 from RUN-2026-06-21-01 — do **not** silently close. |
| `gmail-mercury-abc-finet` | gmail | ABC ACH 5310: 10-05 23513.70, 09-25 2397.39, 06-30 18597.57; FINET 1324: 5558.00 on 10-28, 09-28, 08-28, 07-30, 07-15; peer FYI HH Forecast Fact Check Phase0 2.8; SoR is #64 |
| `gmail-opengov-licensing` | gmail `noreply@opengov.com` | PA-539 + OP-1297 attachment notices 09-28, 10-05, 10-06 |
| `fleet-64-ops-page` | unverified – Page draft only | peer SoR pointer only; no peer-ops receipt file in this repo. Settlement amounts Proven via `gmail-mercury-abc-finet` |
| `box-utah-tap-liquor` | `/workspace/overnight-portfolio/tax/utah-tap/` | `DABS-LIQUOR-CONFIRM-RECIPIENT-FINDINGS-2026-11-02.md` |

## Stale

| ID | URL / path | Notes |
|---|---|---|
| `drive-bond-insurance-tracker` | https://docs.google.com/spreadsheets/d/13BLDfV8TJJpYQwCbKTOBACpZnKWn3j2SsW0LaDNUEN8 | Live Drive read 2026-11-02. Title: *HH - Utah DABS PA-539 Consignment Bond & Insurance Master Tracker (2026 Cycle)*. Drive `modifiedTime` `2026-08-24T16:22:34Z` — **Stale as of 2026-08-24**. Tab `00 README & Status` still: issued=NO, submitted=NO, acceptance=NO, premium=NO; overall state **RED**. Contract/site/instrument rows cited in [FACTS.md](FACTS.md) as **Stale-as-of-tracker only**. |
| `drive-workflow-part1` | https://docs.google.com/document/d/1NHYP7eQ4Gsq-_5owngkJm-ZtP98JlIurGfQ9LfyzSQo | mod 2026-08-09 |
| `drive-okr-notebooklm-export` | https://docs.google.com/document/d/1E1di3OoL35v4pSlcZDsJ_iTn9Mh3fYAF0sFLM4jKrpE | export only |
| `drive-bond-quote-emails` | drive search `Utah DABS PA-539 package agency bonds` | Jul 27–30 2026 |
| `github-dabs-automation` | https://github.com/Hills-and-Hollows/dabs-automation | SoR layout landed in #46 (`73c18365`, 2026-11-02). History of previously tracked `.env.quickbooks` still needs a separate Approve. |

## Proven-candidate

Not Proven. Not DABS acceptance. Live metadata only.

| ID | URL / path | Notes |
|---|---|---|
| `drive-travelers-108566928` | https://drive.google.com/file/d/1gBJIgvlz2c4v2gX3NM2W55T7auwTeTFU/view | Live Drive metadata 2026-11-02. Name: `HH-DABS-Travelers-Consignment-Liquor-Bond-#108566928-$55,000_2026-08-27.pdf`. `createdTime` `2026-08-30T16:52:21Z`; `modifiedTime` `2026-08-30T17:11:10Z`. **May supersede** tracker `issued=NO` for the **$55,000 consignment** instrument only. Do **not** claim DABS submission or acceptance. No later candidate for the $1,000 licensee bond. Scanned PDF (no text layer). |

## Missing

| ID | URL / path | Notes |
|---|---|---|
| `drive-part2-linkaudit-surety-pdf` | *(null in receipt)* | not on first search page; re-verify with `nextPageToken`. Do not treat `drive-travelers-108566928` as this Missing row. |
| `official-dabs-rules` | *(null in receipt)* | **not fetched/frozen**. Stale tracker cites statute/admin-rule IDs — do **not** copy those as official DABS rules. |
| `dabs-portal` | *(null in receipt)* | login-walled. Scorecard Instructions names the portal **Utah DABS OpenGov**; that does not grant portal access or Proven portal payload. |
| `notebooklm-live` | *(null in receipt)* | no connector |
| `hh-dabs-skills` | *(null in receipt)* | none in workflows |

## Confluence — Missing / Blocked

**Status: Missing / Blocked.** Atlassian connector is not installed yet.

- Do **not** invent Confluence space keys, page IDs, or URLs.
- Do **not** treat remembered wiki titles (or tracker-tab Confluence folder cells) as Proven.
- Re-index after the connector is installed; amend this file in a follow-up commit.
- InstallPlugin = **separate Approve only**.

## Receipt gaps (copied, not expanded)

- official rule book freeze SHA
- portal access/export
- live NotebookLM
- bond tracker still Stale (not rewritten as current coverage)
- DABS acceptance of Travelers #108566928 **Unknown**
- $1,000 licensee instrument: no later candidate
- repo docs vs Drive/official reconcile
- no DABS skills
- `.env.quickbooks` history purge is a later Approve

## Scorecard gap hygiene (Proven sheet, do not silently close)

Live Gap Tracker rows from RUN-2026-06-21-01, all **Status=Open** as of the 2026-11-02 read:

| Gap ID | Section | Validation flag | Severity |
|---|---|---|---|
| GAP-001 | C: Required Attachments | Signed RGIS count sheet | High |
| GAP-002 | C: Required Attachments | PA-539 inventory submission | High |
| GAP-003 | B: License/Record Status | Surety/cash bond adequacy | Medium |
| GAP-004 | External | QBO/ACH accounting alignment ($5,558.00; June $5,562.00) | Medium |

Weekly Run Log rows from RUN-2026-06-21-02 through RUN-2026-11-02-01 show **Open Gaps Count=0** while those four Gap rows remain Open. Do **not** change Gap Status from this PR.

Fleet comment on receipt: https://github.com/ShawnOwen/fleet-board/issues/65#issuecomment-6583982494
