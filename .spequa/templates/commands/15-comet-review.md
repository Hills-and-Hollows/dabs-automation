---
description: "Delegate a full PR review to the Comet browser sidecar assistant. Connects to Comet, navigates to the PR on GitHub, dispatches the 14-gate review checklist, and returns a structured verdict."
handoffs:
  - label: Pipeline
    agent: spequa.0-pipeline
    prompt: Resume pipeline after Comet review
  - label: Close Spec
    agent: spequa.16-close
    prompt: Close the spec after PR merge
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the user input. Expected formats:

- `<PR_URL>` — full GitHub PR URL (e.g., `https://github.com/EQUAStart/spequa/pull/39`)
- `<PR_NUMBER>` — PR number only (e.g., `39`); resolved via `gh pr view`
- `<PR_URL> --spec <NNN>` — PR URL with spec number for artifact storage
- `--spec <NNN>` — spec number only; PR URL resolved from current branch via `gh pr view`

If no PR URL or number is provided, attempt to detect from the current branch:
```bash
gh pr view --json url,number -q '{url,number}'
```

## Project Configuration

Read `.spequa/config.yml` if it exists. Use `pipeline.comet` values:

```yaml
pipeline:
  comet:
    enabled: true              # if false, abort with message
    review_timeout: 120        # seconds for sidecar review
    agent_id_prefix: "pipeline" # prefix for Comet agent IDs
    fallback_on_failure: true  # if true, non-fatal on Comet failure
```

If config is missing, use the defaults shown above.

## Purpose

This is the **Comet Browser PR Review** command — a standalone review workflow that uses the Comet browser sidecar assistant to review a pull request on GitHub. It can be invoked:

1. **Standalone**: `/spequa.15-comet-review 39` — ad-hoc review of any PR
2. **From the pipeline**: Phase 7.5 of `/spequa.0-pipeline` delegates to this command
3. **Before merge**: As a pre-merge quality gate with browser-verified evidence

The command produces a structured `comet-review-report.md` with a verdict (APPROVED / CHANGES_REQUIRED / INCONCLUSIVE) and gate-by-gate findings.

## Phase 1: Pre-Flight

### 1.1 Resolve PR Details

```bash
gh pr view <PR_NUMBER> --json url,number,title,headRefName,state,statusCheckRollup
```

Extract:
- `PR_URL` — the full GitHub URL
- `PR_NUMBER` — the PR number
- `PR_TITLE` — for logging
- `BRANCH_NAME` — to derive spec number if not provided
- `PR_STATE` — must be OPEN (warn if MERGED or CLOSED)
- `CI_STATUS` — check rollup for pre-context

### 1.2 Resolve Spec Directory

If `--spec NNN` was provided, use `specs/NNN-*/` as the artifact directory.
Otherwise, derive from `BRANCH_NAME` (e.g., `012-pipeline-comet-control` → `specs/012-pipeline-comet-control/`).
If no spec directory found, write artifacts to the current directory.

### 1.3 Check Comet Configuration

Read `pipeline.comet.enabled` from config. If `false`:
```
[COMET-REVIEW] Comet integration is disabled in .spequa/config.yml. Aborting.
```
Exit without error (non-blocking when called from pipeline with `fallback_on_failure: true`).

## Phase 2: Connect to Comet

### 2.1 Establish CDP Session

Call `comet_connect` with:
- `agentId`: `"<agent_id_prefix>-<spec_number>"` (e.g., `"pipeline-012"`)
- `taskThreadId`: `"review-<spec_number>"` (e.g., `"review-012"`)

This creates an isolated tab group for this review session.

### 2.2 Handle Connection Failure

If `comet_connect` fails (CDP port 9222 unreachable, browser not running, timeout):

```
[COMET-REVIEW] Comet browser not available (CDP connection failed). 
```

If `fallback_on_failure` is true: exit gracefully with a `comet-review-report.md` containing:
```
VERDICT: INCONCLUSIVE
Reason: Comet browser not available — CDP connection failed
```

If `fallback_on_failure` is false: exit with error.

## Phase 3: Navigate and Review

### 3.1 Write Dispatch Instruction

Write `SPEC_DIR/comet-dispatch.json` as an audit artifact:

```json
{
  "task": "pr-review",
  "pr_url": "<PR_URL>",
  "pr_number": <PR_NUMBER>,
  "spec_id": "<NNN>",
  "agent_id": "<agent_id>",
  "timeout": <review_timeout>,
  "timestamp": "<ISO 8601>"
}
```

### 3.2 Navigate to PR

Call `comet_navigate` with the PR URL. Wait for the page to load.

### 3.3 Dispatch Review Checklist to Sidecar

Call `comet_ask` with:
- `sidecar`: `true`
- `timeout`: `<review_timeout * 1000>` (milliseconds)
- `prompt`:

```
You are reviewing PR #<PR_NUMBER> for spec <NNN>.
The PR is open at: <PR_URL>

Please review this pull request against the following 14-gate checklist.
For each gate, evaluate what you can see on this page and in the diff.
Click through to the "Files changed" tab to review the actual code diff.

## Review Checklist

1. **Branch Naming**: Does the branch follow NNN-feature-name convention?
2. **Commit Messages**: Do commits use conventional format (feat:, fix:, chore:)?
3. **Spec Artifacts**: Are spec.md, plan.md, tasks.md present in the PR?
4. **Task Completion**: Are all tasks marked as complete in tasks.md?
5. **Test Coverage**: Are there new/modified test files for new functionality?
6. **Linter Clean**: Check CI status — are lint checks passing?
7. **Security**: No hardcoded secrets, credentials, or API keys in the diff?
8. **Cross-Platform**: If scripts were added, do both bash and PowerShell versions exist?
9. **Template Integrity**: No template markers ([TODO], [NEEDS CLARIFICATION]) in final code?
10. **Constitution Compliance**: Does the implementation follow project principles?
11. **Documentation**: Were relevant docs updated (README, CHANGELOG, etc.)?
12. **CHANGELOG**: Is there a CHANGELOG entry if version-impacting changes were made?
13. **CI Pipeline**: Are CI checks configured and passing?
14. **Diff Review**: Is the code clean, well-structured, with no obvious issues?

## Response Format

Respond with EXACTLY this format:

VERDICT: APPROVED or CHANGES_REQUIRED or INCONCLUSIVE
GATES_PASSED: N/14
FINDINGS:
- [Branch Naming]: PASS or FAIL — brief explanation
- [Commit Messages]: PASS or FAIL — brief explanation
- [Spec Artifacts]: PASS or FAIL — brief explanation
- [Task Completion]: PASS or FAIL — brief explanation
- [Test Coverage]: PASS or FAIL — brief explanation
- [Linter Clean]: PASS or FAIL — brief explanation
- [Security]: PASS or FAIL — brief explanation
- [Cross-Platform]: PASS or FAIL — brief explanation
- [Template Integrity]: PASS or FAIL — brief explanation
- [Constitution Compliance]: PASS or FAIL — brief explanation
- [Documentation]: PASS or FAIL — brief explanation
- [CHANGELOG]: PASS or FAIL — brief explanation
- [CI Pipeline]: PASS or FAIL — brief explanation
- [Diff Review]: PASS or FAIL — brief explanation

If all 14 gates pass, use VERDICT: APPROVED.
If any gate fails, use VERDICT: CHANGES_REQUIRED.
If you cannot evaluate (page not loaded, diff not visible, etc.), use VERDICT: INCONCLUSIVE.
```

### 3.4 Capture Evidence Screenshot

After the sidecar responds, call `comet_screenshot` to capture the PR page state. Save to `SPEC_DIR/evidence/comet-review.png` (create `evidence/` directory if needed).

## Phase 4: Parse and Report

### 4.1 Parse Sidecar Response

Parse the `comet_ask` response text:

- **VERDICT line**: Extract `APPROVED`, `CHANGES_REQUIRED`, or `INCONCLUSIVE`
- **GATES_PASSED line**: Extract `N/14`
- **Finding lines**: Extract gate name, status (PASS/FAIL), and details for each

If the response does not match the expected format, set verdict to `INCONCLUSIVE` and include the raw response in the report.

### 4.2 Write Review Report

Write `SPEC_DIR/comet-review-report.md`:

```markdown
# Comet Review Report

**PR**: <PR_URL>
**PR Number**: #<PR_NUMBER>
**Spec**: <NNN>
**Verdict**: <APPROVED|CHANGES_REQUIRED|INCONCLUSIVE>
**Gates Passed**: <N>/14
**Reviewed By**: Comet Sidecar (Perplexity AI)
**Timestamp**: <ISO 8601>

## Gate Results

- **Branch Naming**: PASS|FAIL — details
- **Commit Messages**: PASS|FAIL — details
[...one line per gate...]

## Evidence

- [comet-review.png](evidence/comet-review.png) — PR page screenshot at review time

## Raw Response

<collapsed raw sidecar response for audit purposes>
```

### 4.3 Report Verdict

Output the verdict clearly:

**If APPROVED**:
```
[COMET-REVIEW] ✓ PR #<NUMBER> APPROVED — <N>/14 gates passed
[COMET-REVIEW] Report: <SPEC_DIR>/comet-review-report.md
```

**If CHANGES_REQUIRED**:
```
[COMET-REVIEW] ✗ PR #<NUMBER> CHANGES REQUIRED — <N>/14 gates passed
[COMET-REVIEW] Failing gates:
  - <gate>: <details>
  - <gate>: <details>
[COMET-REVIEW] Report: <SPEC_DIR>/comet-review-report.md
```

**If INCONCLUSIVE**:
```
[COMET-REVIEW] ? PR #<NUMBER> INCONCLUSIVE — review could not be completed
[COMET-REVIEW] Report: <SPEC_DIR>/comet-review-report.md
```

## Phase 5: Pipeline Integration

When invoked from `/spequa.0-pipeline` Phase 7.5:

### 5.1 Return Control to Pipeline

The pipeline reads `comet-review-report.md` after this command completes and acts on the verdict:

| Verdict | Pipeline Action |
|---------|----------------|
| **APPROVED** | Proceed to Phase 8 (deploy/close) |
| **CHANGES_REQUIRED** | Enter self-correction retry loop — fix failing gates, re-push, re-run `/spequa.15-comet-review` |
| **INCONCLUSIVE** | Proceed with pipeline self-review only (non-blocking) |

### 5.2 Audit Trail Entry

The pipeline appends to `audit-trail.md`:

```markdown
### Comet Review
- **Command**: /spequa.15-comet-review <PR_NUMBER> --spec <NNN>
- **Tool Calls**: comet_connect, comet_navigate, comet_ask(sidecar: true), comet_screenshot
- **Verdict**: <verdict>
- **Gates Passed**: N/14
- **Report**: comet-review-report.md
- **Evidence**: evidence/comet-review.png
- **Timestamp**: <ISO 8601>
```

## Standalone Usage

When invoked outside the pipeline:

```
/spequa.15-comet-review 39
/spequa.15-comet-review https://github.com/EQUAStart/spequa/pull/39
/spequa.15-comet-review --spec 012
/spequa.15-comet-review 39 --spec 012
```

The command is self-contained — it does not require a pipeline run to be active. Results are written to the spec directory (if found) or current directory.
