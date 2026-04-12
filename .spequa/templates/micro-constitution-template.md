# Micro-Constitution: [SPEC_ID]-[FEATURE_NAME]

**Generated**: [TIMESTAMP]
**Immutable**: This document cannot be modified during the pipeline run. If scope changes are needed, the pipeline must pause, a new constitution must be generated, and the run restarts from Phase 0.

## Run Configuration

| Field | Value |
|-------|-------|
| **Spec ID** | [NNN] |
| **Feature Name** | [FEATURE_NAME] |
| **Problem Statement** | [USER_DESCRIPTION] |
| **Target Repository** | [REPO_PATH] |
| **Branch Convention** | [NNN]-[feature-name] from [BASE_BRANCH] |
| **Autonomy Level** | [HIGH\|MEDIUM\|LOW] |
| **Timeout** | [N] minutes |
| **Deploy Target** | [production\|staging\|none] |
| **Score Threshold** | [N]/[applicable] |
| **Max Retries Per Phase** | [N] |

## Quality Standards

- **Gate requirement**: 14-gate PR checklist passes, CI green, 0 security findings
- **Test requirement**: All existing tests pass, new tests added for new acceptance criteria
- **Doc requirement**: Score >= 9.0 on 5-dimension rubric (Accuracy, Completeness, Cross-References, Clarity, Maintainability)

## Constitution Constraints

<!--
  Inherited from project constitution (.spequa/memory/constitution.md).
  List the specific principles that apply to this run.
-->

[CONSTITUTION_CONSTRAINTS]

## Success Criteria

<!--
  Copied from spec.md — the SC-NNN items this run must satisfy.
  Populated after Phase 1 (Spequafy) generates the spec.
-->

[SUCCESS_CRITERIA]
