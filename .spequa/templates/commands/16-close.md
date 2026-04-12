---
description: Validate spec completion, capture evidence artifacts via browser automation, and formally close the spec after PR merge.
scripts:
  sh: scripts/bash/close-spec.sh --json "{ARGS}"
  ps: scripts/powershell/close-spec.ps1 -Json "{ARGS}"
---

<!-- config-refs: test_command -->

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The input should contain a spec number (e.g., `005`) or feature name (e.g., `005-spec-closure`).

## Project Configuration

Before executing, read `.spequa/config.yml` if it exists. Use configured values where this command references them below; if the file is missing or a key is absent, use the inline default shown in parentheses after each reference.

Also check `.spequa/overrides/close/` for phase override files. This command has phases A, B, C, D, E. For each phase:
- `phase-a-pre.md` — read and insert immediately before Phase A
- `phase-a.md` — read and use instead of Phase A entirely
- `phase-a-post.md` — read and insert immediately after Phase A
- (same pattern for phases b, c, d, e)

If an override file references a phase that does not exist (e.g., `phase-z.md`), warn and skip it.

If config.yml contains unrecognized keys, warn about each one and suggest the closest valid key name.

## Purpose

This is **Phase 8 (CLOSE)** of the Specification-Driven Development pipeline -- the mandatory final step that runs AFTER a spec's implementing PR has been merged. It validates the implementation against the specification, captures visual evidence, and formally closes the spec with an auditable closure report.

**Constitution Authority**: This command enforces Constitution Article VI (Formal Spec Closure, NON-NEGOTIABLE). No spec may remain in Draft status after its implementing PR has been merged.

## Idempotency

This command is idempotent. On re-run:

- The `evidence/` directory is cleared and all evidence is recaptured fresh
- The `closure-report.md` is overwritten (not versioned with suffixes)
- No stale artifacts from prior runs persist

---

## Phase A: Prerequisites

### Step A1: Locate Spec and Verify Merge

1. Parse `$ARGUMENTS` for the spec number (e.g., `005`).
2. Run `{SCRIPT}` from repo root and parse JSON output for:
   - `SPEC_DIR` -- absolute path to spec directory
   - `SPEC_FILE` -- path to spec.md
   - `PR_URL` -- merged PR URL
   - `MERGE_DATE` -- PR merge date
   - `BASELINE_FILE` -- path to baseline-tests.md (empty if none)
   - `PR_MERGED` -- boolean
   - `MERGE_COMMIT` -- merge commit SHA on the repo default branch (empty if `gh` could not resolve the PR)
   - `DEFAULT_BRANCH` -- repository default branch name (e.g. `main`); use with `git diff` in Phase D

3. **If `PR_MERGED` is false**: HALT immediately with:

   ```text
   [CLOSE] Spec NNN PR has not been merged yet. Merge the PR first, then re-run /spequa.16-close NNN
   ```

### Step A2: Verify Required Artifacts

1. Run `.spequa/scripts/bash/run-closure-checks.sh <SPEC_DIR>` and parse JSON output.

2. **If `overall` is `BLOCKED`**: HALT immediately. Report which files are missing:

   ```text
   [CLOSE] BLOCKED -- Missing required artifacts: [list]. Complete the pipeline first.
   ```

3. **If `overall` is `FAIL`**: Collect all FAIL results but DO NOT halt yet. Continue to Phase B/C/D to gather all findings before generating the report.

4. Store parsed results for use in Phase E (including `MERGE_COMMIT` and `DEFAULT_BRANCH` for the closure report **Release identity** section).
   - `tasks` -- total, completed, incomplete counts
   - `status_field` -- current spec status
   - `markers` -- list of unresolved marker locations
   - `sc_items` -- list of success criteria
   - `fr_items` -- list of functional requirements

### Step A3: Idempotency Setup

1. If `SPEC_DIR/evidence/` exists, clear it completely (remove all files).
2. If `SPEC_DIR/closure-report.md` exists, it will be overwritten in Phase E.

---

## Phase B: Test Comparison

### Step B1: Capture Final Test Snapshot

1. Run `.spequa/scripts/bash/run-baseline-tests.sh .` from repo root to capture the final test results.
2. Parse the output for metrics: Total, Passed, Failed, Skipped.
3. Check the output Status field:
   - If `SKIP` (test runner unavailable or no tests found):
     - **If `BASELINE_FILE` exists**: result is FAIL -- "Test runner unavailable; fix environment before closure."
     - **If no `BASELINE_FILE`**: result is SKIP -- "No baseline and no test runner -- comparison skipped."
   - If tests ran successfully: proceed to Step B2.

### Step B2: Compare Against Baseline

1. If `BASELINE_FILE` is empty or file does not exist:
   - Record comparison as SKIP with note: "No baseline available -- comparison skipped."
   - The Test Comparison section is still included in the closure report (FR-012).
   - Proceed to Phase C.

2. If `BASELINE_FILE` exists:
   - Parse `baseline-tests.md` for metrics: Total, Passed, Failed, Skipped.
   - Compute deltas: `final - baseline` for each metric.
   - If `final_failed > baseline_failed`: flag as WARNING (non-blocking) with the count of new failures.
   - Record the comparison table for Phase E.

---

## Phase C: Success Criteria Verification

### Step C1: Classify SC-* Items

1. Use the `sc_items` extracted in Phase A from `run-closure-checks.sh` JSON output.
2. If no SC-* items were found, Phase A already recorded FAIL ("spec is malformed"). Skip to Phase D.

3. For each SC-* item, classify as:
   - **Objective** -- contains keywords indicating programmatic verifiability: test count, file exists, passes, coverage, time, under, percentage, contains, produces, updated, committed, every, zero, 100%
   - **Subjective** -- all others (qualitative judgments, user experience, readability)

### Step C2: Auto-Verify Objective Items

For each objective SC-* item, attempt automated verification:

- **Test metrics** (e.g., "tests pass", "coverage reaches X%"): Run the project's test command (config: `test_command`, default: `uv run pytest --tb=short -q`) and check output
- **File existence** (e.g., "closure-report.md exists"): Check file path
- **Structural checks** (e.g., "constitution contains Article VI"): Parse file content
- **Count/percentage** (e.g., "100% of specs"): Compute from available data

Record result as: `{id, text, verification_type: "auto", result: "pass"|"fail", notes: "evidence description"}`

### Step C3: Prompt for Subjective Items

For each subjective SC-* item:

1. Present the criterion text to the developer
2. Ask: "Does this criterion pass? (pass / fail / deferred with justification)"
3. Record result as: `{id, text, verification_type: "manual", result: "pass"|"fail"|"deferred", notes: "developer response or justification"}`

**Deferred items are non-blocking** -- they are recorded in the closure report but do not cause an overall FAIL.

---

## Phase D: Visual Evidence Capture

### Step D1: Detect Validation Targets

1. Run `git diff <DEFAULT_BRANCH> --name-only` (use `DEFAULT_BRANCH` from Step A1 JSON; if missing, use `main`) to identify files changed relative to the integration branch.
2. Map changed files to viewable outputs:
   - `docs/*.md` -- documentation pages
   - `src/**/*.py` -- CLI commands (check for Typer/Click commands)
   - `templates/**/*.md` -- template files (viewable as rendered Markdown)
3. Cross-reference with SC-* items that reference viewable outputs (screenshots, UI, pages).
4. If no validation targets found: skip Phase D with notation "No visual validation targets -- evidence capture skipped." (FR-016)

### Step D2: Check Browser Automation Availability

1. Attempt to use Comet/Playwright MCP tools (e.g., `browser_navigate` or `comet-screenshot`).
2. If unavailable or fails: skip Phase D with notation "Browser automation unavailable -- evidence capture skipped." (FR-016)
3. This is non-blocking -- closure proceeds with text-only evidence.

### Step D3: Capture Screenshots

1. Create `SPEC_DIR/evidence/` directory.
2. For each visually verifiable SC-* item:
   - Navigate to the relevant output (doc page, CLI help, test results)
   - Capture screenshot as `evidence/SC-NNN.png` (FR-014)
3. For other validation targets:
   - Capture as `evidence/screenshot-NNN-description.png`
4. If an individual screenshot fails, log the error and continue with remaining captures.

### Step D4: Capture Screen Recording

1. Attempt screen recording via Playwright MCP video capture.
2. If recording not supported: capture sequential screenshots as a visual timeline instead.
3. Save to `evidence/`:
   - If video file is under Git LFS threshold: commit via LFS
   - If video file exceeds threshold: upload to Google Drive and record URL (FR-015)

### Step D5: Generate Evidence Metadata

1. Create `evidence/demo-steps.md` documenting each step taken:

   ```markdown
   # Feature Demonstration: [FEATURE_NAME]

   Captured: [ISO_8601_TIMESTAMP]
   Method: [Comet browser automation / Text-only]

   ## Step 1: [Action description]

   ![Step 1](screenshot-001-description.png)

   **Action**: [What was done]
   **Result**: [What the screenshot shows / expected outcome confirmed]
   ```

---

## Phase E: Report Generation & Closure

### Step E1: FR-to-Task Traceability

1. Use `fr_items` from Phase A (run-closure-checks.sh output).
2. Read `tasks.md` and for each FR-NNN:
   - Search for tasks that reference or implement this requirement (by FR ID, keyword matching, or semantic alignment)
   - Record covering task IDs
3. Any FR with no covering completed task is reported as a GAP (per FR-009 and Constitution Article VI).

### Step E2: Compile Closure Report

1. Read `templates/closure-report-template.md` for the report structure.
2. Determine overall result:
   - **PASS**: All structural checks pass, all SC-* items pass or deferred, FR traceability complete
   - **FAIL**: Any structural check fails, any SC-* item fails, FR gaps exist
   - **BLOCKED**: Should not reach Phase E (caught in Phase A)

3. Fill all sections:
   - **Header**: Spec name, branch, PR URL, merge date, close date
   - **Release identity**: Base branch (`DEFAULT_BRANCH`), merge commit (`MERGE_COMMIT` or note if unknown), and whether root `CHANGELOG.md` was reviewed for this change set (confirm entry or *N/A*)
   - **Summary**: Derived from spec.md overview
   - **Success Criteria Verification**: Table from Phase C
   - **Functional Requirements Coverage**: Table from Step E1
   - **Test Comparison**: Table from Phase B (always present per FR-012)
   - **Evidence Artifacts**: Links from Phase D (or skip notation)
   - **Closure Signature**: Agent identity, ISO 8601 timestamp, "Pipeline Phase: 8/8 CLOSE", overall result

4. Write report to `SPEC_DIR/closure-report.md`.

### Step E3: Update Spec Status

1. In `spec.md`, update the Status field:
   - Change `**Status**: Draft` to `**Status**: Complete`
   - Add `**Closed**: [TODAY in YYYY-MM-DD]` on the line after Status
2. If Status is already `Complete` (re-closure): update the Closed date only.

### Step E4: Commit Closure Artifacts

1. Stage closure artifacts:

   ```bash
   git add SPEC_DIR/closure-report.md
   git add SPEC_DIR/evidence/
   git add SPEC_DIR/spec.md
   ```

2. Commit with conventional format:

   ```bash
   git commit -m "chore(NNN): close spec -- add closure report and evidence"
   ```

3. Push to the base branch if on it, or note that the commit needs to be pushed.

---

## Output

After completion, output a closure summary:

```text
=== SPEC CLOSURE SUMMARY ===
Spec: NNN-feature-name
Status: Complete
Closed: YYYY-MM-DD
Result: PASS / FAIL

Success Criteria: X/Y PASS (Z DEFERRED)
FR Coverage: X/Y COVERED (Z GAPS)
Test Delta: +N tests, +N% coverage
Evidence: N screenshots, demo-steps.md

Merge commit: <MERGE_COMMIT or unknown>
Base branch: <DEFAULT_BRANCH>

Closure Report: specs/NNN-feature/closure-report.md
============================
```

## Error Handling

- **PR not merged**: HALT -- cannot close an unmerged spec
- **Required artifacts missing**: BLOCK -- halt with list of missing files
- **No SC-* items in spec**: FAIL -- spec is malformed
- **Test runner unavailable + baseline exists**: FAIL -- fix environment
- **Test runner unavailable + no baseline**: SKIP -- note in report
- **SC-* item FAIL**: FAIL -- report failures with evidence
- **SC-* item DEFERRED**: Non-blocking -- recorded with justification
- **Comet/Playwright unavailable**: SKIP -- proceed with text-only evidence (non-blocking)
- **No visual targets**: SKIP -- note in report (non-blocking)
- **Git not available**: WARN -- generate report but skip commit step

## Behavior Rules

- **Evidence over assertion**: Every PASS verdict must cite evidence (test output, file path, screenshot). Never mark a criterion as PASS without verification.
- **Graceful degradation**: Comet browser automation enhances but does not gate closure. The closure report is always generated.
- **Idempotent**: Running `/spequa.16-close NNN` on an already-closed spec clears `evidence/`, overwrites `closure-report.md`. No stale artifacts persist.
- **Constitution compliance**: This step enforces the Spec Lifecycle > Formal Closure constitutional principle (Article VI).
