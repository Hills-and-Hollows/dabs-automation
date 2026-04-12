---
description: "Autonomous sequential pipeline loop — generates micro-constitution, executes 10 phases with gate checks, self-corrects on failures, pauses for clarification, and scores against R1-R10 rubric."
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

This is a **fully autonomous sequential pipeline** that runs the complete Spec-Driven Development lifecycle end-to-end. It executes 10 phases (0-9) in strict sequential order, where each phase's output automatically becomes the next phase's input. The pipeline self-corrects on gate failures, pauses only for genuine ambiguities or constitution conflicts, and produces a scored evaluation of the completed work.

**Core guarantee**: A developer provides a feature description and walks away. The pipeline produces a deployed feature with a scorecard — zero intermediate manual actions required.

---

## 1. User Input and Configuration Parsing

### 1.1 Parse Feature Description

Extract the feature description from `$ARGUMENTS`. This is the primary input — the problem statement that drives the entire pipeline.

### 1.2 Parse Optional Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--autonomy` | HIGH / MEDIUM / LOW | HIGH | How aggressively to auto-resolve ambiguity |
| `--timeout` | 15-180 (minutes) | 60 | Max wall-clock time per pipeline run |
| `--deploy-target` | production / staging / none | none | Where to deploy on completion |
| `--score-threshold` | 8-10 | 10 | Minimum passing score (out of applicable requirements) |
| `--max-retries` | 1-5 | 3 | Self-correction attempts before escalating |
| `--resume` | flag (no value) | — | Resume a paused pipeline |
| `--queue` | comma-separated descriptions | — | Batch-process multiple specs sequentially |

### 1.3 Load Configuration Defaults

1. Check for `.spequa/config.yml` in the repo root
2. Read the `pipeline:` section if present:

   ```yaml
   pipeline:
     autonomy_level: "HIGH"
     max_retries_per_phase: 3
     timeout_minutes: 60
     deploy_target: "none"
     score_threshold: 10
     pause_on_destructive: true
   ```

3. CLI flags override config.yml values. Config.yml overrides built-in defaults.

### 1.4 If --queue Flag Is Present

Skip to **Section 20: Spec Queue** below. Queue mode wraps the entire pipeline in a loop.

### 1.5 If --resume Flag Is Present

Skip to **Section 16: Resume Logic** below.

---

## 2. Pre-Flight Validation

Before any phase executes, validate the environment.

### 2.1 Clean Working Tree (FR-018)

```bash
git status --porcelain
```

- If output is **non-empty**: STOP immediately. Report: `[PIPELINE] REJECTED: Working tree is dirty. Commit or stash changes before running the pipeline.`
- If output is **empty**: proceed.

### 2.2 Concurrency Lock (FR-017)

```bash
scripts/bash/check-concurrent-runs.sh --json --feature-dir
```

- If another pipeline run is active (lock held by a live process): STOP immediately. Report: `[PIPELINE] REJECTED: Another pipeline run is active (PID: <pid>). Wait for it to complete or release the lock.`
- If lock is stale (PID no longer running): acquire lock and proceed.
- If no lock exists: acquire lock and proceed.

### 2.3 Record Start Time

Record the current timestamp. All timeout checks compare elapsed time against `config.timeout_minutes` from this moment.

---

## 3. Phase 0: Trigger / Micro-Constitution (FR-002, FR-008)

**Purpose**: Generate the immutable contract that governs all agent behavior for this run.

### 3.1 Auto-Detect Spec Number (FR-007)

Determine the next available spec number by checking:

1. Existing directories in `specs/` (e.g., `specs/001-*`, `specs/002-*`)
2. Local branches matching `NNN-*` pattern
3. Remote branches matching `NNN-*` pattern

Use the highest number found + 1. Format as zero-padded 3-digit string (e.g., `009`).

### 3.2 Generate Micro-Constitution

Create `specs/NNN-feature-name/micro-constitution.md` from `templates/micro-constitution-template.md`.

Fill all required fields:

| Field | Source |
|-------|--------|
| Spec ID | Auto-detected (step 3.1) |
| Feature Name | Derived from user's feature description (slug format) |
| Problem Statement | User's original description verbatim |
| Target Repository | Current repo path |
| Branch Convention | `{NNN}-{feature-name}` from `{branch_from}` |
| Autonomy Level | From config (section 1) |
| Timeout | From config (section 1) |
| Deploy Target | From config (section 1) |
| Score Threshold | From config (section 1) |
| Quality Standards | Inherited from `.spequa/memory/constitution.md` |
| Constitution Constraints | Key principles from `.spequa/memory/constitution.md` |
| Success Criteria | Populated after Phase 1 (spec generates SC-NNN items) |

### 3.3 Initialize Pipeline State

```bash
scripts/bash/pipeline-state.sh init --spec-id NNN --feature-name "feature-name" --config '{"autonomy_level":"HIGH","max_retries_per_phase":3,"timeout_minutes":60,"deploy_target":"none","score_threshold":10,"pause_on_destructive":true}'
```

This creates `.pipeline-state.json` in the feature directory with status `running`, all phases set to `pending`, empty decisions/retries arrays, and the concurrency lock.

### 3.4 Initialize Audit Trail

Create `specs/NNN-feature-name/audit-trail.md` from `templates/audit-trail-template.md`. Add the first entry:

```markdown
## Phase 0: Trigger
- **Started**: [ISO 8601 timestamp]
- **Completed**: [ISO 8601 timestamp]
- **Gate Result**: PASS
- **Artifacts**: micro-constitution.md, .pipeline-state.json, audit-trail.md
```

### 3.5 Gate Check

- **PASS condition**: All required micro-constitution fields are populated (non-empty).
- **FAIL action**: Identify which fields are missing. If the user's description is too vague to derive a problem statement, enter the retry loop (section 14).
- **PAUSE condition**: Never — Phase 0 always has user input.

### 3.6 Report Progress

```text
[PIPELINE] Phase 0/9 COMPLETE: trigger ✓ → Proceeding to Phase 1: spequafy
```

---

## 4. Phase 1: Spequafy

**Purpose**: Create the feature specification, requirements checklist, and baseline test results.

### 4.1 Create Branch and Scaffold

Run `{SCRIPT}` from repo root (the `create-new-feature.sh` invocation from frontmatter). Parse the JSON output for `BRANCH_NAME`, `SPEC_FILE`, `FEATURE_NUM`, `FEATURE_DIR`. All paths must be absolute.

### 4.2 Write Specification

Read `templates/spec-template.md` and write `spec.md` in the feature directory:

- Fill all sections from the user's feature description
- Create prioritized user stories (P1, P2, P3) with independent test criteria
- Define measurable success criteria (SC-NNN)
- Define functional requirements (FR-NNN)
- For areas where information is insufficient, mark `[NEEDS CLARIFICATION]` (max 3)

### 4.3 Generate Requirements Checklist

Create `FEATURE_DIR/checklists/requirements.md` using `templates/checklist-template.md`. Validate requirements quality — each requirement must be testable, unambiguous, and traceable.

### 4.4 Run Baseline Tests

```bash
scripts/bash/run-baseline-tests.sh
```

Record the baseline test results. These are compared against at implementation completion to detect regressions.

### 4.5 Update Micro-Constitution

Add the Success Criteria (SC-NNN items) from the spec to the micro-constitution's Success Criteria section. This is the **only** permitted modification — all other fields are immutable.

### 4.6 Gate Check

- **PASS condition**: All spec sections complete. Zero `[TODO]` markers. All user stories have independent test criteria. All success criteria are measurable.
- **FAIL action**: Identify incomplete sections. Auto-fill from the user's description or infer from codebase context. Retry.
- **PAUSE condition**: The user's description is too ambiguous to produce a complete spec even after inference.

### 4.7 Save and Report

Save state via `pipeline-state.sh update`. Append audit trail entry. Report:

```text
[PIPELINE] Phase 1/9 COMPLETE: spequafy ✓ → Proceeding to Phase 2: clarify
```

---

## 5. Phase 2: Clarify

**Purpose**: Scan for ambiguities and resolve them per the autonomy level matrix.

### 5.1 Scan for Ambiguities

Read the spec and identify:

- All `[NEEDS CLARIFICATION]` markers
- Implicit ambiguities (requirements that could be interpreted multiple ways)
- Missing edge cases
- Undefined behavior for error conditions

### 5.2 Apply Autonomy Level Matrix (FR-012)

For EACH ambiguity, execute this resolution sequence:

**Step A — Context Research**:

- Scan the existing codebase for patterns, conventions, and prior decisions
- Read `.spequa/memory/constitution.md` for relevant principles
- Check existing specs in `specs/` for precedent decisions
- Analyze the tech stack, dependencies, and project structure

**Step B — Expert Decision Analysis**:

- Identify ALL viable options (typically 2-5)
- For each option evaluate: alignment with project patterns, risk, effort, best practices
- Score each option on these dimensions

**Step C — Confidence Evaluation and Resolution**:

| Scenario | HIGH Autonomy | MEDIUM Autonomy | LOW Autonomy |
|----------|---------------|-----------------|--------------|
| Evidence clearly supports one option (>70% confidence) | Auto-resolve | Auto-resolve | **PAUSE** |
| No clear winner, no strong evidence | Auto-resolve (best guess) | **PAUSE** | **PAUSE** |
| Architecture-level decision | Auto-resolve | **PAUSE** | **PAUSE** |
| Constitution conflict | **PAUSE** (always) | **PAUSE** (always) | **PAUSE** (always) |
| Destructive operation | Check `pause_on_destructive` | **PAUSE** | **PAUSE** |

**For auto-resolved decisions**: Replace `[NEEDS CLARIFICATION]` with the chosen approach. Log the decision:

- Question, answer, confidence level, evidence (file:line citations)
- Write to both `.pipeline-state.json` decisions array and `audit-trail.md`

**For PAUSE decisions**: Enter the Pause Handler (section 15).

### 5.3 Gate Check

- **PASS condition**: Zero unresolved high-impact questions remain.
- **FAIL action**: Re-examine unresolved items with broader search scope. Retry.
- **PAUSE condition**: Confidence below threshold per autonomy level.

### 5.4 Save and Report

```text
[PIPELINE] Phase 2/9 COMPLETE: clarify ✓ → Proceeding to Phase 3: research
```

---

## 6. Phase 3: Research

**Purpose**: Extract unknowns from the spec and resolve them through codebase research.

### 6.1 Extract Unknowns

Read the spec and identify:

- Technical unknowns (library choices, API designs, data models)
- Integration points with existing code
- Performance implications
- Security considerations

### 6.2 Research Codebase

For each unknown:

- Search the codebase for related patterns and prior implementations
- Check existing specs for precedent decisions
- Identify reusable components, utilities, and patterns
- Document findings with file:line citations

### 6.3 Generate Research Artifact

Create `FEATURE_DIR/research.md` with:

- Each unknown identified
- Research findings with citations
- Recommended approach with rationale
- Alternatives considered and why they were rejected

### 6.4 Gate Check

- **PASS condition**: All `NEEDS_CLARIFICATION` markers resolved with evidence-backed answers.
- **FAIL action**: Research with different search strategies (broader keywords, adjacent files, git history). Retry.
- **PAUSE condition**: Conflicting evidence requires human judgment.

### 6.5 Save and Report

```text
[PIPELINE] Phase 3/9 COMPLETE: research ✓ → Proceeding to Phase 4: plan
```

---

## 7. Phase 4: Plan

**Purpose**: Generate the technical implementation plan, data model, and contracts.

### 7.1 Setup Plan

```bash
scripts/bash/setup-plan.sh --json
```

Parse JSON output for `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH`.

### 7.2 Generate Plan Artifacts

Read the completed spec, research.md, and `.spequa/memory/constitution.md`. Generate:

1. **plan.md** — Full implementation plan following `templates/plan-template.md`:
   - Technical context (language, dependencies, storage, testing)
   - Constitution check (verify compliance with all Articles)
   - Project structure with file paths
   - Phase-by-phase implementation approach
   - Complexity tracking

2. **data-model.md** — Entity schemas, relationships, state machines (if applicable)

3. **contracts/** — API contracts, interface definitions (if applicable)

### 7.3 Update Agent Context

```bash
scripts/bash/update-agent-context.sh --agent-type <detected_agent>
```

### 7.4 Gate Check

- **PASS condition**: Plan covers 100% of acceptance criteria from the spec. Constitution check passes. All artifacts generated (plan.md and data-model.md at minimum).
- **FAIL action**: Identify uncovered acceptance criteria. Add plan sections to address them. Retry.
- **PAUSE condition**: Architecture decision with no clear winner, or constitution violation detected.

### 7.5 Save and Report

```text
[PIPELINE] Phase 4/9 COMPLETE: plan ✓ → Proceeding to Phase 5: tasks
```

---

## 8. Phase 5: Tasks

**Purpose**: Generate the dependency-ordered task breakdown.

### 8.1 Load Prerequisites

```bash
scripts/bash/check-prerequisites.sh --json
```

Parse JSON for `FEATURE_DIR` and `AVAILABLE_DOCS`. Load plan.md, spec.md, data-model.md, and all generated artifacts.

### 8.2 Generate Tasks

Create `tasks.md` following `templates/tasks-template.md`:

- Organize tasks by user story (P1 then P2 then P3)
- Use strict checklist format: ``- [ ] **TaskID** [labels] description — `file/path` ``
- Mark parallel-safe tasks with `[P]`
- Include dependency graph showing which tasks block which
- Map every acceptance criterion to at least one task
- Map every task to at least one acceptance criterion

### 8.3 Gate Check

- **PASS condition**: Every acceptance criterion maps to at least one task. Every task maps to at least one acceptance criterion. No circular dependencies. All tasks have file paths.
- **FAIL action**: Add missing tasks for uncovered ACs, or remove orphan tasks. Retry.
- **PAUSE condition**: Task estimation uncertainty exceeds 4 hours (MEDIUM/LOW autonomy only).

### 8.4 Save and Report

```text
[PIPELINE] Phase 5/9 COMPLETE: tasks ✓ → Proceeding to Phase 6: implement
```

---

## 9. Phase 6: Implement

**Purpose**: Execute the task plan — write code, tests, and documentation.

### 9.1 Pre-Implementation Checks

1. Scan `FEATURE_DIR/checklists/` for checklist files. Count completed vs incomplete items.
   - All pass: proceed
   - Non-blocking incomplete: proceed with note
   - Blocking incomplete: STOP for human
2. Check for extension hooks: `before_implement` in `.spequa/config.yml` — execute if present.

### 9.2 Execute Tasks Sequentially

Process tasks in dependency order from `tasks.md`:

1. **Setup tasks**: Project structure, dependencies, configuration files
2. **Foundational tasks**: Blocking prerequisites (data models, base classes)
3. **User story tasks**: Implement each story in priority order (P1, P2, P3)
   - Write tests first (if test-first approach specified in plan)
   - Models, then services, then endpoints, then integration
4. **Polish tasks**: Cross-cutting concerns, documentation updates

For each task:

- Execute the implementation
- Mark as `[x]` in tasks.md when complete
- If a task fails: attempt recovery. Log the failure. If unrecoverable after 3 attempts, enter the pause handler.
- For parallel tasks `[P]`: execute them, report any failures separately

### 9.3 Post-Implementation Checks

1. Check extension hooks: `after_implement` in `.spequa/config.yml` — execute if present.
2. Run the full test suite. All tests must pass.
3. Scan for `TODO` and `FIXME` markers in new/modified code — zero allowed.

### 9.4 Gate Check

- **PASS condition**: All tasks marked `[x]`. All tests pass. Zero `TODO`/`FIXME` in new code.
- **FAIL action**: Fix failing tests or incomplete tasks. Remove or resolve TODO markers. Retry.
- **PAUSE condition**: Constitution conflict in implementation approach, or security concern requiring human review.

### 9.5 Save and Report

```text
[PIPELINE] Phase 6/9 COMPLETE: implement ✓ → Proceeding to Phase 7: review
```

---

## 10. Phase 7: Review

**Purpose**: Run the full PR review checklist, documentation quality gate, and create the pull request.

### 10.1 Run 14-Gate PR Checklist

Execute the complete checklist from `templates/commands/create-pull-request.md`:

1. Branch naming convention
2. Commit message format
3. Spec artifact completeness
4. Task completion (100%)
5. Test coverage
6. Linter passes (ruff, markdownlint)
7. Security scan (no leaked credentials, no hardcoded secrets)
8. Cross-platform parity (bash + powershell if applicable)
9. Template integrity (no template markers remain)
10. Constitution compliance
11. Documentation updates
12. CHANGELOG entry (if applicable)
13. CI pipeline configuration
14. Self-review diff walkthrough

### 10.2 Documentation Quality Gate

If standard doc files were modified (README.md, CHANGELOG.md, docs/*):

```bash
scripts/bash/score-docs-ci.sh
```

- Composite score must be >= 9.0 with no individual dimension < 8
- If gate fails: fix documentation gaps automatically, re-score
- Record results in `FEATURE_DIR/doc-scores.md`

### 10.3 Structural Validation

Run doc structural validation per `templates/commands/docs.md`:

- Cross-reference integrity (no broken links)
- Audience boundary compliance (user docs contain no dev-only content)

### 10.4 Create Pull Request

1. Stage all changes: `git add -A`
2. Create commit: `git commit -m "feat(NNN): implement <feature-name>"`
3. Push: `git push -u origin <BRANCH_NAME>`
4. Create PR via `gh pr create`:
   - **Title**: `feat: <feature-name> (Spec NNN)`
   - **Body**: Auto-generated from spec.md, plan.md, tasks.md — feature overview, user stories, technical approach, task completion summary, checklist results, spec link
   - **Base**: repository default branch
   - **Head**: feature branch

### 10.5 Comet Browser Review (if enabled)

After the PR is created and pushed, delegate a full browser-based review via the standalone Comet review command:

**Step 1 — Check Configuration**:

Read `.spequa/config.yml` for `pipeline.comet.enabled`. If Comet is disabled, skip this section entirely and proceed to Gate Check.

**Step 2 — Invoke `/spequa.15-comet-review`**:

Execute the standalone Comet review command:

```
/spequa.15-comet-review <PR_NUMBER> --spec <NNN>
```

This command handles the full workflow: connect to Comet, navigate to the PR, dispatch the 14-gate checklist to the sidecar, parse the response, write `comet-review-report.md`, and capture evidence screenshots. See `templates/commands/comet-review.md` for the complete command specification.

**Step 3 — Read Verdict**:

After `/spequa.15-comet-review` completes, read `FEATURE_DIR/comet-review-report.md` and extract the verdict.

**Step 4 — Act on Verdict**:

| Verdict | Action |
|---------|--------|
| **APPROVED** | Log success. Proceed to Gate Check. |
| **CHANGES_REQUIRED** | Log findings. Enter self-correction retry loop to address the failing gates. After fixes, re-push and re-run `/spequa.15-comet-review`. |
| **INCONCLUSIVE** | Log warning: "Comet review inconclusive — proceeding with pipeline self-review only." Proceed to Gate Check. |

**Step 5 — Log to Audit Trail**:

Append to `audit-trail.md`:

```markdown
### Comet Review
- **Command**: /spequa.15-comet-review <PR_NUMBER> --spec <NNN>
- **Verdict**: [APPROVED|CHANGES_REQUIRED|INCONCLUSIVE]
- **Gates Passed**: N/14
- **Report**: comet-review-report.md
- **Timestamp**: [ISO 8601]
```

### 10.6 Gate Check

- **PASS condition**: All 14 gates pass. CI green (or CI not configured — excluded). PR created successfully. Comet review APPROVED or INCONCLUSIVE (non-blocking).
- **FAIL action**: Fix gate failures (lint errors, test failures, doc scores). Retry.
- **PAUSE condition**: Security finding requiring human review.

### 10.7 Save and Report

```text
[PIPELINE] Phase 7/9 COMPLETE: review ✓ → Proceeding to Phase 8: deploy
```

---

## 11. Phase 8: Deploy

**Purpose**: Deploy and verify (or skip if deploy_target is none).

### 11.1 Check Deploy Target

Read `deploy_target` from micro-constitution:

- If `none`: Mark phase as **skipped** in pipeline state. Report and advance:

  ```text
  [PIPELINE] Phase 8/9 SKIPPED: deploy (deploy_target=none) → Proceeding to Phase 9: score
  ```

- If `staging` or `production`: proceed to deployment.

### 11.2 Execute Deployment

Deploy using the project's deployment mechanism (detected from project structure — e.g., `deploy.sh`, CI/CD pipeline trigger, platform CLI).

### 11.3 Verify Health Check

After deployment, verify the service is healthy:

- Hit the health endpoint (if web service)
- Run smoke tests (if configured)
- Check deployment logs for errors

### 11.4 Gate Check

- **PASS condition**: Health check passes (or phase skipped).
- **FAIL action**: Check deployment logs, fix configuration issues, retry deployment.
- **PAUSE condition**: Deploy environment unavailable or health check fails after max retries.

### 11.5 Comet Evidence Capture (if enabled)

If Comet was connected during Phase 7 and `pipeline.comet.evidence_capture` is true:

1. **Navigate to merged PR**: Call `comet_navigate` with the PR URL.
2. **Capture screenshot**: Call `comet_screenshot` and save the result to `FEATURE_DIR/evidence/pr-merged.png`.
3. **Capture CI status**: If CI checks are visible, call `comet_screenshot` and save to `FEATURE_DIR/evidence/ci-status.png`.
4. **Log evidence capture**: Append to `audit-trail.md`:

```markdown
### Evidence Capture
- **Tool Calls**: comet_navigate(PR_URL), comet_screenshot()
- **Screenshots**: evidence/pr-merged.png, evidence/ci-status.png
- **Timestamp**: [ISO 8601]
```

If Comet is unavailable: skip with notation "Browser automation unavailable — evidence capture skipped" (non-blocking per Constitution Article VI).

### 11.6 Save and Report

```text
[PIPELINE] Phase 8/9 COMPLETE: deploy ✓ → Proceeding to Phase 9: score
```

---

## 12. Phase 9: Score

**Purpose**: Evaluate the completed pipeline run against the R1-R10 rubric.

### 12.1 Generate Scorecard

```bash
scripts/bash/generate-scorecard.sh --spec-dir FEATURE_DIR --state-file .pipeline-state.json
```

This evaluates each requirement against concrete artifacts:

| # | Requirement | Check Method | Excluded When |
|---|-------------|--------------|---------------|
| R1 | Autonomous Execution | Audit trail shows zero manual phase transitions | Never |
| R2 | Spec Completeness | spec.md has all required fields, zero TODOs | Never |
| R3 | Clarification Resolution | All decisions have evidence or were human-resolved | Never |
| R4 | Plan-to-Spec Traceability | tasks.md maps every AC to task and vice versa | Never |
| R5 | Implementation Correctness | Tests pass, no TODOs in code, ACs addressed | Never |
| R6 | CI/CD Pipeline Green | CI checks pass at merge time | No CI configured |
| R7 | 14-Gate PR Review | PR checklist passes | Never |
| R8 | Deployment Verification | Health check passes post-deploy | deploy_target=none |
| R9 | Self-Correction Integrity | All retries used different approaches, within budget | No retries occurred (auto-PASS) |
| R10 | Audit Trail and Scorecard | All phases have entries, all decisions cite evidence | Never |

### 12.2 Determine Verdict

Calculate: `score = total_passed / total_applicable`

| Score | Verdict | Action |
|-------|---------|--------|
| N/N (100%) | PRODUCTION_READY | Pipeline complete. Report success. |
| >= threshold | CONDITIONAL_PASS | Identify lowest-scoring requirement. Loop back to re-execute its phase. Re-score. Max 1 loop-back. |
| >= 50% but < threshold | NEEDS_REMEDIATION | Pause pipeline. Set status `paused`. Generate diagnostic report. Surface to user. |
| < 50% | CRITICAL_FAILURE | Set status `failed`. Generate post-mortem. Surface to user. |

### 12.3 Conditional Pass Loop-Back

If verdict is CONDITIONAL_PASS:

1. Identify the requirement with the lowest score (the FAIL item closest to PASS)
2. Determine which phase is responsible for that requirement
3. Re-execute that single phase with the explicit goal of satisfying the failing requirement
4. Re-run scoring
5. This loop-back happens at most once. If still not PRODUCTION_READY after one loop-back, set verdict to NEEDS_REMEDIATION and pause.

### 12.4 Write Scorecard

Generate `FEATURE_DIR/scorecard.md` from `templates/scorecard-template.md` with:

- Run metadata (run ID, timestamps, configuration)
- Per-requirement verdicts with proof artifact links
- Diagnostics for each FAIL (root cause, what would achieve PASS)
- Execution summary (duration, phases completed, retries used, decisions made)

### 12.5 Gate Check

- **PASS condition**: Score >= threshold (after any loop-back).
- **FAIL action**: Loop-back (if not yet attempted) or escalate.
- **PAUSE condition**: N/A — this is the final phase.

### 12.6 Save and Report

Release the concurrency lock. Set pipeline status to `completed` (or `failed`/`paused` per verdict).

```text
[PIPELINE] Phase 9/9 COMPLETE: score ✓ — Pipeline finished with verdict: PRODUCTION_READY
```

---

## 13. Sequential Phase Loop Engine

This is the core execution model. For each phase 0 through 9, the pipeline executor performs these steps in order:

### 13.1 Check Idempotent Skip

Read `.pipeline-state.json`. If this phase's status is `completed` or `skipped`, skip it entirely. This enables idempotent resume after pause or crash.

### 13.2 Check Timeout (FR-014)

Calculate elapsed time since pipeline start. If elapsed >= `config.timeout_minutes`:

1. Save current state
2. Set pipeline status to `paused`
3. Set pause reason to `timeout`
4. Release concurrency lock
5. Report: `[PIPELINE] TIMEOUT: Pipeline exceeded {N} minute limit at Phase {current}. Run with --resume to continue.`
6. STOP execution.

### 13.3 Execute Phase

Run the phase logic as defined in sections 3-12 above.

### 13.4 Evaluate Gate

Each phase produces a gate result: **PASS**, **FAIL**, or **PAUSE**.

- **PASS**: Save state (mark phase completed, record artifacts). Append audit trail entry (phase name, timestamps, gate result, artifacts produced). Advance to next phase.
- **FAIL**: Enter Self-Correction Retry Loop (section 14).
- **PAUSE**: Enter Pause Handler (section 15).

### 13.5 Report Progress

After each successful phase:

```text
[PIPELINE] Phase N/9 COMPLETE: <phase_name> ✓ → Proceeding to Phase N+1: <next_phase>
```

After the final phase:

```text
[PIPELINE] Pipeline run complete. Verdict: <verdict>. Score: <passed>/<applicable>.
```

---

## 14. Self-Correction Retry Loop (FR-004)

When a gate returns FAIL, the pipeline enters this loop:

### 14.1 Increment Retry Count

Read current `retry_count` for this phase from `.pipeline-state.json`. If `retry_count >= config.max_retries_per_phase`:

1. Generate a diagnostic report covering all retry attempts (diagnoses, strategies, outcomes)
2. Set pipeline status to `paused`
3. Set pause reason to `retry_exhausted`
4. Release concurrency lock
5. Surface the diagnostic report to the user with resume instructions
6. STOP execution

### 14.2 Diagnose Root Cause

Analyze the gate failure to identify the **root cause**, not just the symptom. For example:

- Symptom: "test_auth_flow fails" → Root cause: "auth middleware missing token refresh logic"
- Symptom: "spec section 3 is empty" → Root cause: "user description did not mention persistence layer"

### 14.3 Apply Graduated Retry Strategy

| Retry # | Strategy | Approach |
|----------|----------|----------|
| 1 | **Targeted fix** | Fix the specific failure identified by the gate check |
| 2 | **Assumption re-examination** | Re-read the previous phase's output for misinterpretation or missed context |
| 3 | **Alternative approach** | Broader scope — consider a fundamentally different approach to the entire phase |

### 14.4 Verify Differentiation

Before executing each retry: compare the planned approach against all previous attempts for this phase. The retry **must be measurably different** — not an identical re-execution. Log the differentiation rationale.

### 14.5 Log Retry

Append to both `.pipeline-state.json` retries array and `audit-trail.md`:

- Phase number and attempt number
- Failure diagnosis (root cause)
- Strategy chosen and how it differs from previous attempts
- Outcome (resolved or failed)
- Timestamp

### 14.6 Re-Execute and Re-Gate

Re-run the phase logic. Re-evaluate the gate. If PASS, exit the retry loop and continue normal execution. If FAIL, loop back to step 14.1.

---

## 15. Pause Handler (FR-006, FR-009)

When a gate returns PAUSE or a constitution conflict is detected:

### 15.1 Save Pause State

Write to `.pipeline-state.json`:

- `pause.active`: true
- `pause.phase`: current phase number
- `pause.reason`: one of `clarification`, `constitution_conflict`, `timeout`, `retry_exhausted`, `destructive_op`
- `pause.question`: the specific question (if clarification)
- `pause.options`: 2+ resolution options with evidence
- `pause.paused_at`: ISO 8601 timestamp

Set pipeline status to `paused`.

### 15.2 Release Lock

Release the concurrency lock so other operations are not blocked.

### 15.3 Surface Question to User

Present to the user:

- The specific question or conflict
- 2+ resolution options with pros/cons and supporting evidence
- The agent's recommended option with reasoning (if applicable)
- Why this decision requires human judgment
- Context about what the pipeline has completed so far

### 15.4 Provide Resume Instructions

```text
[PIPELINE] Phase N/9 PAUSED: <phase_name> — Human Decision Required

To resume: Run /spequa.0-pipeline --resume
Provide your answer to the question above when resuming.
```

### 15.5 STOP Execution

The pipeline stops here. No further phases execute until the user resumes.

---

## 16. Resume Logic

When `--resume` flag is present:

### 16.1 Locate Pipeline State

Find the `.pipeline-state.json` file by scanning `specs/*/` directories for one with `pause.active: true`.

### 16.2 Validate Pause State

- If no paused pipeline found: Report `[PIPELINE] No paused pipeline found. Start a new run without --resume.` and STOP.
- If `pause.active` is not `true`: Report the same and STOP.

### 16.3 Acquire Lock

Run concurrency lock acquisition. If another run has taken the lock, STOP.

### 16.4 Process User's Answer

If the pause reason was `clarification` or `constitution_conflict`:

1. Read the user's answer from `$ARGUMENTS` (the text after `--resume`)
2. Encode the answer into the relevant artifact (spec.md, plan.md, etc.)
3. Log the decision as a human-resolved entry in `.pipeline-state.json` and `audit-trail.md`

### 16.5 Clear Pause and Resume

1. Set `pause.active` to `false`
2. Clear `pause.question`, `pause.options`, `pause.paused_at`
3. Set pipeline status to `running`
4. Detect completed phases from state (all phases with status `completed` or `skipped`)
5. Resume execution from `pause.phase` — re-enter the Sequential Phase Loop (section 13) starting at the paused phase

---

## 17. Constitution Conflict Detection (FR-009)

At **every decision point** throughout the pipeline, validate the proposed action against:

1. **micro-constitution.md** — the run-scoped contract (section 3)
2. **`.spequa/memory/constitution.md`** — the project-level principles

### 17.1 Conflict Triggers

A constitution conflict exists when:

- A proposed implementation violates a constitutional Article
- A clarification resolution contradicts a constitutional principle
- A design decision is incompatible with established constraints
- Scope has changed beyond what the micro-constitution permits

### 17.2 Conflict Resolution

Constitution conflicts **always trigger PAUSE** regardless of autonomy level. This is non-negotiable.

When a conflict is detected:

1. Identify the specific Article or principle being violated
2. Explain the conflict clearly
3. Present options: modify the approach to comply, or request a constitution amendment
4. Enter the Pause Handler (section 15) with reason `constitution_conflict`

---

## 18. Autonomy Level Matrix (FR-012)

This matrix governs all decision-making throughout the pipeline:

| Scenario | HIGH | MEDIUM | LOW |
|----------|------|--------|-----|
| Clarification with codebase evidence (>70% confidence) | Auto-resolve | Auto-resolve | PAUSE |
| Clarification without strong evidence | Auto-resolve (best guess with rationale) | PAUSE | PAUSE |
| Architecture decision | Auto-resolve | PAUSE | PAUSE |
| Constitution conflict | PAUSE (always) | PAUSE (always) | PAUSE (always) |
| Destructive operation (force push, delete, overwrite) | Check `pause_on_destructive` config | PAUSE | PAUSE |

**All auto-resolved decisions** must be logged with: question, answer, confidence, evidence (file:line citations), and timestamp. No silent decisions.

---

## 19. Audit Trail (FR-015)

The audit trail is an append-only Markdown file at `FEATURE_DIR/audit-trail.md`.

### 19.1 Phase Entries

After each phase completion, append:

```markdown
## Phase N: <name>
- **Started**: <ISO 8601>
- **Completed**: <ISO 8601>
- **Duration**: <HH:MM:SS>
- **Gate Result**: PASS | FAIL (retry N) | SKIPPED
- **Artifacts**: <comma-separated list of files produced>
- **Retry Count**: <N>
```

### 19.2 Decision Entries

For auto-resolved decisions:

```markdown
### Decision: <short description>
- **Phase**: <N>
- **Question**: <the ambiguity>
- **Resolution**: Auto-resolved
- **Answer**: <chosen option>
- **Confidence**: <HIGH|MEDIUM> (<percentage>)
- **Evidence**: <file:line citation>
- **Timestamp**: <ISO 8601>
```

For human-resolved decisions:

```markdown
### Decision: <short description>
- **Phase**: <N>
- **Question**: <the ambiguity>
- **Resolution**: Human-resolved
- **Options Presented**: <list>
- **Answer**: <user's choice>
- **Timestamp**: <ISO 8601>
```

### 19.3 Retry Entries

```markdown
### Retry: Phase <N>, Attempt <M>
- **Diagnosis**: <root cause>
- **Strategy**: <approach taken>
- **Differentiation**: <how this differs from previous attempt>
- **Outcome**: Resolved | Failed
- **Timestamp**: <ISO 8601>
```

### 19.4 Dual Persistence

All decisions and retries are also written to the corresponding arrays in `.pipeline-state.json` for programmatic access by scripts and resume logic.

---

## 20. Spec Queue (FR-013)

When `--queue` flag is present with comma-separated feature descriptions:

### 20.1 Initialize Queue

1. Parse the comma-separated descriptions into an ordered list
2. Create `.pipeline-queue.json` at the repo root:

   ```json
   {
     "queue_id": "queue-<unix_timestamp>",
     "specs": [
       {"input": "<description>", "spec_id": null, "status": "pending", "scorecard_path": null}
     ],
     "current_index": 0,
     "halted_reason": null
   }
   ```

### 20.2 Process Queue Sequentially

For each spec in the queue:

1. Set the spec's status to `running` and update `current_index`
2. Run the **full pipeline** (sections 2-12) for this spec independently — its own branch, artifacts, micro-constitution, and scorecard
3. After scoring, check the verdict:
   - **PRODUCTION_READY**: Set spec status to `completed`. Advance to next spec.
   - **CONDITIONAL_PASS** (after loop-back): Set spec status to `completed`. Advance to next spec.
   - **Below threshold** (NEEDS_REMEDIATION or CRITICAL_FAILURE): Set spec status to `halted`. Set `halted_reason`. STOP the queue — do not advance to next spec.
   - **Paused** (clarification needed): Set spec status to `paused`. STOP the queue. User must resume this spec before the queue continues.

### 20.3 Queue Summary

After all specs complete (or queue halts), report:

```text
=== QUEUE SUMMARY ===
Queue ID: <id>
Total Specs: <N>
Completed: <N>
Failed/Halted: <N>
Remaining: <N>

Spec 1: <description> — PRODUCTION_READY (10/10) — specs/NNN-feature/scorecard.md
Spec 2: <description> — HALTED (6/10) — specs/NNN-feature/scorecard.md
Spec 3: <description> — PENDING (not started)
=====================
```

---

## 21. Exit Conditions (FR-016)

The pipeline terminates when ANY of these conditions is met:

1. **Score meets threshold**: Verdict is PRODUCTION_READY or CONDITIONAL_PASS (after loop-back). Status: `completed`.
2. **Max retries exhausted**: A phase failed `max_retries_per_phase` times with escalation. Status: `paused` (awaiting human input).
3. **Timeout exceeded**: Wall-clock time exceeds `timeout_minutes`. Status: `paused` (can resume).
4. **User abort**: User terminates the session. State is saved; can resume later.
5. **NEEDS_REMEDIATION**: Score is 50-below-threshold%. Status: `paused`.
6. **CRITICAL_FAILURE**: Score below 50%. Status: `failed`.

On ANY termination, the pipeline:

1. Saves current state to `.pipeline-state.json`
2. Appends final entry to `audit-trail.md`
3. Releases the concurrency lock
4. Outputs the Final Report (section below)

---

## 22. Behavioral Rules

These rules are **non-negotiable** and apply throughout all phases:

1. **NEVER fabricate** requirements, constraints, code patterns, or technical decisions (FR-010). All decisions must be derived from the codebase, the spec, or the user's input.

2. **NEVER modify the micro-constitution** during a run (FR-008). The only exception is adding Success Criteria after Phase 1 spec generation.

3. **Save artifacts to disk after EVERY phase** (FR-005). A crash or timeout must lose at most one phase of work.

4. **All decisions must cite evidence**. Auto-resolved decisions cite codebase evidence (file:line). Human-resolved decisions cite the user's input.

5. **Phase outputs automatically feed the next phase** (FR-001). No manual transfer, no copy-paste, no agent switching.

6. **Constitution is non-negotiable**. Never auto-resolve in a way that violates constitution principles. Constitution conflicts always PAUSE — regardless of autonomy level.

7. **Research before asking**. Always attempt autonomous resolution via codebase research, expert analysis, and pattern matching before pausing for human input.

8. **Every retry must be different**. Identical re-execution wastes the retry budget. Each attempt must use a measurably different approach.

9. **Idempotent execution**. If a phase is already complete (per state file), skip it. Never re-execute completed phases during resume.

10. **Transparency over speed**. Log all decisions, retries, and gate results. The audit trail must be complete enough for post-run review.

---

## Pipeline Status Reporting

At each phase transition, output a compact status line:

```text
[PIPELINE] Phase N/9 COMPLETE: <phase_name> ✓ → Proceeding to Phase N+1: <next_phase>
```

When stopping for human input:

```text
[PIPELINE] Phase N/9 PAUSED: <phase_name> ⏸️ — Human Decision Required
```

When a phase is skipped:

```text
[PIPELINE] Phase N/9 SKIPPED: <phase_name> (reason) → Proceeding to Phase N+1: <next_phase>
```

---

## Final Report

After the pipeline terminates (by any exit condition), output:

```text
=== PIPELINE SUMMARY ===
Feature: <name>
Spec ID: <NNN>
Branch: <branch_name>
Spec: <spec_path>
PR: <pr_url> (or "N/A — pipeline paused at Phase N")
Scorecard: <scorecard_path> (or "N/A — pipeline did not reach scoring")
Verdict: <PRODUCTION_READY | CONDITIONAL_PASS | NEEDS_REMEDIATION | CRITICAL_FAILURE | PAUSED | TIMED_OUT>
Score: <passed>/<applicable>
Phases Completed: N/10
Auto-Resolved Decisions: X
Human Decisions Required: Y
Retries Used: Z across M phases
Total Duration: HH:MM:SS
========================
```
