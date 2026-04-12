<!--
Sync Impact Report
==================
Version change: 0.0.0 (template) → 1.0.0 (initial ratification)
Added principles:
  - I. Pricing Accuracy (NEW)
  - II. Utah Regulatory Compliance (NEW)
  - III. Scraper Resilience (NEW)
  - IV. Test-First for Pricing Logic (NEW)
  - V. Inventory Reconciliation (NEW)
  - VI. Observability and Alerting (NEW)
Added sections:
  - Technology Stack
  - Development Workflow
  - Spec Lifecycle (retained)
  - Governance (populated)
Removed sections: None
Templates requiring updates:
  - .spequa/templates/plan-template.md ✅ compatible
  - .spequa/templates/spec-template.md ✅ compatible
  - .spequa/templates/tasks-template.md ✅ compatible
  - .spequa/templates/commands/*.md ✅ no agent-name hardcoding found
Follow-up TODOs: None
-->

# DABS-Automation Constitution

## Core Principles

### I. Pricing Accuracy

Liquor pricing data sourced from the Utah Department of Alcoholic
Beverage Services (DABS) MUST be captured and republished with a
sustained error rate below 0.1%.

- All monetary values MUST use `Decimal(19,4)` precision.
  Floating-point arithmetic is prohibited for any price, cost,
  margin, or tax calculation.
- Markups, taxes, and case-pricing math MUST be applied via
  Decimal-safe libraries.
- Every published price MUST be traceable to its source DABS
  record (URL, snapshot date, raw value) for audit.
- Price changes between sync runs MUST be recorded as deltas,
  not silent overwrites; historical pricing MUST be queryable.

**Rationale**: H&H pricing decisions, customer quotes, and
margin reporting all depend on this data. A 0.1% error rate at
volume becomes thousands of dollars per quarter.

### II. Utah Regulatory Compliance

The system MUST maintain 100% compliance with Utah DABS
regulatory requirements at all times.

- License renewals, permit deadlines, and regulatory submissions
  MUST be tracked with calendar reminders. Missed deadlines are
  treated as P0 incidents.
- The system MUST NOT republish or redistribute DABS data in
  any way that violates DABS terms of use.
- All scraping activity MUST respect DABS robots.txt and rate
  limits; aggressive scraping is prohibited.
- Compliance documentation (license copies, correspondence,
  filings) lives in Google Drive under
  `~/Documents/1. ORGANIZATIONS/1.1 HH/`, never in this repo.

**Rationale**: Operating without a valid liquor license shuts
down the business. Compliance is non-negotiable.

### III. Scraper Resilience

DABS web data acquisition MUST be designed for change. The
upstream site is not a contract; the scraper is.

- Each scraper MUST have a smoke test that detects DOM/structure
  drift and fails loudly before bad data is published.
- Scrapers MUST use retry-with-backoff for transient failures
  and circuit-break on sustained failures.
- A failed scrape MUST NOT silently fall back to stale data;
  staleness MUST be surfaced as an explicit alert.
- Data validators MUST reject obviously malformed records
  (negative prices, missing SKUs, impossible dates) at the
  ingest boundary.

**Rationale**: A silent scraper failure publishes stale prices
that drive bad decisions. Loud failure is always preferred.

### IV. Test-First for Pricing Logic

Any code path that produces a published price or inventory
record MUST be covered by tests written before the
implementation.

- Pricing math (markup, tax, case math, conversions) MUST have
  unit tests with known-good fixtures from real DABS data.
- Scraper parsers MUST have fixture-based tests using captured
  HTML snapshots so changes are detectable in CI.
- Integration tests MUST hit a real PostgreSQL test database;
  DB mocks are prohibited for pricing or inventory code.
- A failing test MUST exist before implementation begins.

**Rationale**: Pricing bugs are silent failures that compound
across thousands of records before anyone notices.

### V. Inventory Reconciliation

Inventory state in this system MUST be reconciled against
authoritative sources on a defined cadence.

- DABS-published inventory MUST be reconciled against this
  system's snapshot daily.
- Internal H&H inventory counts MUST be reconciled against
  procurement and sales records weekly.
- Reconciliation discrepancies MUST be raised as
  `NEEDS_RESOLUTION` records — never silently auto-resolved.
- Bulk imports MUST be safe to re-run without duplicating
  records (idempotent on natural keys).

**Rationale**: Inventory drift compounds. Without forced
reconciliation, the system slowly diverges from reality.

### VI. Observability and Alerting

All scraping, pricing, and reconciliation jobs MUST emit
structured logs with correlation IDs and alert on anomalies.

- Logs MUST be JSON, not free-form text.
- Every job run MUST emit a summary record: rows processed,
  rows published, deltas detected, rows rejected, with
  rejected-row context.
- Anomalous deltas (e.g., a 50% price swing on a SKU) MUST
  trigger an alert even if individually valid.
- Failed runs MUST notify the operator, not just log silently.

**Rationale**: A pricing system that fails quietly is worse
than no system at all.

## Technology Stack

- **Language**: Python 3.11+
- **Web framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Testing**: pytest with fixture-based scraper tests
- **Tooling**: Install with `uv tool install` — never with
  system pip. macOS system Python is too old.
- **Browser automation** (when needed): Comet via comet-bridge
  MCP only. Selenium, Playwright, and Puppeteer are prohibited
  per workspace constitution.
- **Scheduling**: Cron or APScheduler for recurring jobs;
  long-running jobs SHOULD be idempotent.

## Development Workflow

- **Branches**: `###-feature-name` matching the spec number.
- **Commits**: Atomic, descriptive, one logical change per
  commit.
- **PRs**: MUST reference the originating spec number; the
  `/spequa.13-code-review` checklist MUST pass before merge.
- **Force push**: Permitted on feature branches, prohibited on
  `main` and `staging`.
- **Secrets**: Environment variables only. Never commit API
  keys, database URLs, or credentials.
- **Specs**: Live in `specs/` with numbered directories. Each
  spec tracks its own plan, tasks, and closure report.

## Spec Lifecycle

### Formal Closure (NON-NEGOTIABLE)

Every specification that reaches PR merge MUST undergo formal
closure validation before the spec is considered complete.
Closure requires:

1. **Verification**: All success criteria (SC-NNN) verified with
   evidence.
2. **Coverage**: All functional requirements (FR-NNN) traced to
   completed tasks.
3. **Evidence**: Visual or textual evidence of the working
   implementation captured. Pricing-related closures MUST
   include sample published records compared against DABS source.
4. **Status Update**: Spec status field updated from Draft to
   Complete with closure date.
5. **Closure Report**: A `closure-report.md` generated in the
   spec directory using `templates/closure-report-template.md`.

No spec may remain in Draft status after its implementing PR has
been merged.

## Governance

This constitution is the authoritative source of project rules
for the dabs-automation repository. It is subordinate to the
Hills and Hollows workspace constitution and MUST NOT contradict
its terms; where the workspace constitution is silent, this
document governs.

- **Amendments** require documented rationale, version bump, and
  propagation to dependent templates. Run
  `/spequa.1-constitution` to apply.
- **Versioning** follows semver: MAJOR for principle removal or
  redefinition, MINOR for new principles or material expansions,
  PATCH for clarifications and typos.
- **Compliance** is verified during plan-phase Constitution
  Checks and PR code review gates.

**Version**: 1.0.0 | **Ratified**: 2026-04-12 | **Last Amended**: 2026-04-12
