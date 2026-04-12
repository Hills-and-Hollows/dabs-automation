# Pipeline Scorecard: [SPEC_ID]-[FEATURE_NAME]

**Run ID**: [RUN_ID]
**Completed**: [TIMESTAMP]
**Score**: [PASS_COUNT]/[APPLICABLE_COUNT]
**Verdict**: [PRODUCTION_READY|CONDITIONAL_PASS|NEEDS_REMEDIATION|CRITICAL_FAILURE]

## Requirements

| # | Requirement | Verdict | Proof |
|---|-------------|---------|-------|
| R1 | Autonomous Execution | [PASS\|FAIL] | [Link to audit-trail.md — zero manual phase transitions] |
| R2 | Spec Completeness | [PASS\|FAIL] | [Link to spec.md — all fields populated, zero TODOs] |
| R3 | Clarification Resolution | [PASS\|FAIL] | [Link to audit-trail.md decisions — all resolved with evidence] |
| R4 | Plan-to-Spec Traceability | [PASS\|FAIL] | [Link to tasks.md — every AC mapped to task and vice versa] |
| R5 | Implementation Correctness | [PASS\|FAIL] | [Link to test results and code diff — all ACs addressed] |
| R6 | CI/CD Pipeline Green | [PASS\|FAIL\|EXCLUDED] | [Link to CI run or "excluded: no CI configured"] |
| R7 | 14-Gate PR Review | [PASS\|FAIL] | [Link to PR checklist — all 14 gates pass] |
| R8 | Deployment Verification | [PASS\|FAIL\|EXCLUDED] | [Link to health check or "excluded: deploy_target=none"] |
| R9 | Self-Correction Integrity | [PASS\|FAIL] | [Link to audit-trail.md retry entries — all different approaches] |
| R10 | Audit Trail & Scorecard | [PASS\|FAIL] | [This file + audit-trail.md — all phases have entries] |

## Diagnostics

<!--
  For each FAIL requirement: describe root cause and what would be needed to achieve PASS.
  For EXCLUDED requirements: document why they were excluded.
  Leave empty if all requirements PASS.
-->

[DIAGNOSTICS]

## Execution Summary

| Metric | Value |
|--------|-------|
| **Total Duration** | [HH:MM:SS] |
| **Phases Completed** | [N]/10 |
| **Phases Skipped** | [N] |
| **Retries Used** | [N] across [M] phases |
| **Decisions Auto-Resolved** | [N] |
| **Decisions Human-Resolved** | [N] |
| **Pauses** | [N] |
