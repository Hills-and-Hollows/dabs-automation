# Closure Report: [FEATURE_NAME]

**Spec**: [NNN-feature-name]
**Branch**: [BRANCH_NAME]
**PR**: [PR_URL]
**Spec Created**: [CREATED_DATE]
**PR Merged**: [MERGE_DATE]
**Closed**: [CLOSE_DATE]
**Result**: [PASS | FAIL | BLOCKED]

## Release identity

| Field | Value |
|-------|--------|
| **Base branch** | [DEFAULT_BRANCH — from close-spec JSON] |
| **Merge commit (on base branch)** | [40-char SHA from `MERGE_COMMIT`, or *unknown — supply via `gh pr view <url> --json mergeCommit` if empty] |
| **CHANGELOG** | [Confirmed: root `CHANGELOG.md` documents this change set / *N/A — internal or docs-only*] |

## Summary

[2-3 sentence summary of what was built, derived from spec.md overview.]

## Success Criteria Verification

| ID | Criterion | Type | Status | Evidence |
|----|-----------|------|--------|----------|
| SC-001 | [criterion text] | auto / manual | PASS / FAIL / DEFERRED | [link to evidence or description] |

## Functional Requirements Coverage

| ID | Requirement | Covering Tasks | Status |
|----|-------------|----------------|--------|
| FR-001 | [requirement summary] | T1, T2 | COVERED / GAP |

## Test Comparison

| Metric | Baseline | Final | Delta |
|--------|----------|-------|-------|
| Total tests | [N] | [N] | [+/-N] |
| Passed | [N] | [N] | [+/-N] |
| Failed | [N] | [N] | [+/-N] |
| Skipped | [N] | [N] | [+/-N] |
| Coverage | [N%] | [N%] | [+/-N%] |

**Baseline source**: [baseline-tests.md path or "No baseline available -- comparison skipped"]

## Evidence Artifacts

<!--
  List all captured evidence artifacts below.
  If Comet browser automation was available, this includes screenshots and demo walkthrough.
  If Comet was unavailable, text-only descriptions are provided.
  If no visual targets exist, note the skip reason.
-->

| File | Type | Mapped Check | Storage |
|------|------|-------------|---------|
| evidence/SC-001.png | screenshot | SC-001 | git |
| evidence/demo-steps.md | metadata | full flow | git |

**Evidence capture method**: [Comet browser automation / Text-only (Comet unavailable) / Skipped (no visual targets)]

## Closure Signature

- **Closed by**: [AGENT_IDENTITY]
- **Timestamp**: [ISO_8601_TIMESTAMP]
- **Pipeline Phase**: 8/8 CLOSE
- **Gate Result**: [PASS / FAIL / BLOCKED]
