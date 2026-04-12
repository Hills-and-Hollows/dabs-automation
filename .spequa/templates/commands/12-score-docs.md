---
description: "Scorecard Benchmark Rubric for formal scoring of all audited spequa documentation."
handoffs:
  - label: Docs Validation
    agent: spequa.11-docs
  - label: Create Pull Request
    agent: spequa.14-create-pull-request
---

Documentation Quality Rubric

Formal scoring framework for auditing Spequa documentation. Use this rubric for ongoing reviews and when closing spec work that touches docs.

## Scoring Dimensions (5 x 10pts = 50pts max)

### 1. Accuracy (10pts)

Does every statement match the actual codebase behavior?

| Score | Criteria |
|-------|----------|
| 10 | Every command, path, flag, and behavior description verified against source code |
| 8 | All major facts correct; minor details (e.g., an option flag name) may be slightly off |
| 5 | Core workflow is correct but several specifics are wrong or outdated |
| 2 | Doc describes behavior that doesn't exist or contradicts the code |

How to verify: Spot-check 3+ commands/paths against AGENT_CONFIG, `spequa-common.sh`, or actual script behavior.

### 2. Completeness (10pts)

Does the doc cover everything its audience needs?

| Score | Criteria |
|-------|----------|
| 10 | All features, options, edge cases, and error scenarios documented |
| 8 | Core features fully covered; 1-2 edge cases missing |
| 5 | Happy path documented but no error handling, troubleshooting, or alternatives |
| 2 | Covers only a fragment of the topic; reader left with unanswered questions |

How to verify: Can a new user complete the task described using only this doc?

### 3. Cross-References (10pts)

Does the doc link to related docs and avoid dead ends?

| Score | Criteria |
|-------|----------|
| 10 | Links to all related docs; no dead links; "See also" or "Next Steps" section present |
| 8 | Links to primary related docs; no dead links |
| 5 | Some links present but key related docs not referenced |
| 2 | Isolated doc with no outbound links; reader must guess what to read next |

How to verify: Click every link. Check if `pipeline.md`, `installation.md`, and `quickstart.md` are referenced where relevant.

### 4. Clarity (10pts)

Is the doc easy to scan, understand, and act on?

| Score | Criteria |
|-------|----------|
| 10 | Clear headings, tables for structured data, code blocks for commands, callouts for warnings, consistent formatting |
| 8 | Well-organized with minor formatting inconsistencies |
| 5 | Readable but walls of text, missing code blocks, or inconsistent heading levels |
| 2 | Disorganized, ambiguous language, mixing concepts without structure |

How to verify: Can someone scan the headings alone and understand the doc's structure?

### 5. Maintainability (10pts)

Will this doc stay accurate as the project evolves?

| Score | Criteria |
|-------|----------|
| 10 | No hardcoded counts/lists that go stale; references source of truth (e.g., AGENT_CONFIG); AGENTS.md integration guide updated |
| 8 | Mostly resilient; 1-2 values that could go stale |
| 5 | Several hardcoded values that will break on next agent addition or feature change |
| 2 | Entire doc will be wrong after the next release |

How to verify: If a new agent is added tomorrow, what breaks? If a command is renamed, what breaks?

## Composite Score

| Formula | Range | Grade |
|---------|-------|-------|
| Sum of 5 dimensions / 50 x 10 | 0-10 | See below |

| Composite | Grade | Meaning |
|-----------|-------|---------|
| 9.5-10.0 | Ship | Production-ready, no improvements needed |
| 8.0-9.4 | Polish | Good, but has specific gaps to address before merge |
| 6.0-7.9 | Rework | Significant issues; must fix before closing the spec |
| < 6.0 | Rewrite | Fundamentally incomplete or inaccurate |

## Target Benchmarks

| Milestone | Target | Notes |
|-----------|--------|-------|
| Merge to main | >= 9.0 composite | No individual dimension below 8 |
| Spec close | >= 9.5 composite | All dimensions 9+ |
| Quarterly audit | >= 9.0 composite | Re-score all docs, fix any drift |

## Audit Process

### Per-Spec Audit (at spec close)

1. List all docs modified or referenced by the spec
2. Score each doc on all 5 dimensions
3. Fix any dimension scoring < 8 before merge
4. Record scores in the spec's `tasks.md` as a verification checkpoint

### Quarterly Audit (ongoing)

1. Re-score every doc in `docs/` and root-level `.md` files
2. Compare against previous quarter's scores
3. File issues for any doc that dropped below 9.0
4. Prioritize accuracy and cross-reference fixes (most likely to drift)

### Automated Checks (CI-enforceable)

- All internal markdown links resolve (no dead links)
- Every doc in `docs/` is listed in `toc.yml`
- Every doc in `docs/` is listed in `docs/README.md`
- Agent count in tables matches AGENT_CONFIG key count
- No `[NEEDS CLARIFICATION]` markers in published docs
