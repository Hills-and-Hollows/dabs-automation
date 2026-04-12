---
description: Create a pull request after implementing a spec, with pre-flight validation, documentation quality gate, and self-review checklist.
handoffs:
  - label: Review PR
    agent: spequa.13-code-review
    prompt: Review the pull request
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

# Post-Implementation PR Creation Instructions

You have just finished implementing a spec. Before creating your Pull Request, complete every step below in order. Do not skip any step.

## Project Configuration

Check `.spequa/overrides/create-pull-request/` for phase override files. This command has phases 1, 2, 3, 4, 5. For each phase:
- `phase-1-pre.md` — read and insert immediately before Phase 1
- `phase-1.md` — read and use instead of Phase 1 entirely
- `phase-1-post.md` — read and insert immediately after Phase 1
- (same pattern for phases 2, 3, 4, 5)

If an override file references a phase that does not exist, warn and skip it.

***

## Phase 1: Pre-Flight Validation

Run all of these locally and fix any failures before proceeding:

```bash
# 1. Lint (language-specific)
# 2. Run full test suite
# 3. Verify CLI still works (if applicable)
```

Fix every error. Do not proceed with failures.

***

## Phase 1.25: Documentation Structural Validation

Before quality scoring, validate documentation structural integrity using `/spequa.11-docs`.

### Step 1: Run Structural Validation

Execute the `/spequa.11-docs` command. This checks:
- Broken markdown links (CRITICAL)
- Stale file path references (CRITICAL)
- Missing documentation coverage for manifest patterns (WARNING)
- Audience boundary violations — dev-internal content in user docs (CRITICAL)
- Command drift between dev and template command sets (WARNING)

### Step 2: Evaluate Result

- **PASS** (zero CRITICAL issues): Proceed to Phase 1.5 (Doc Quality Gate).
- **FAIL** (one or more CRITICAL issues): HALT. Fix all CRITICAL issues before continuing. Re-run `/spequa.11-docs` to verify fixes.
- **WARNING items**: Report to user. These should be fixed but do not block PR creation. If the user provides explicit justification, log the override and proceed.

### Step 3: Record in PR Description

Note the docs validation result in the PR description:
- `Docs Validation: PASS` or `Docs Validation: PASS (N warnings overridden — [justification])`

***

## Phase 1.5: Documentation Quality Gate

Before proceeding to self-review, assess the quality of any documentation modified by this feature.

### Step 1: Identify Modified Documentation

Run `git diff main --name-only` and filter to the standard documentation set:
- `README.md`, `CHANGELOG.md`, `CLAUDE.md`, `AGENTS.md`
- Any file under `docs/`

Filter out files that no longer exist in the working tree (deleted files).

### Step 2: Determine Gate Applicability

- **If no standard doc files were modified**: SKIP this gate with notation "No documentation files modified — gate skipped." Proceed to Phase 2.
- **If standard doc files were modified**: Continue to Step 3.

### Step 3: Score Each Modified Document

For each modified documentation file, score it against the 5-dimension rubric:

| Dimension | What to Evaluate | Score Range |
|-----------|-----------------|-------------|
| Accuracy | Does every statement match actual codebase behavior? | 1-10 |
| Completeness | Does the doc cover everything its audience needs? | 1-10 |
| Cross-References | Does the doc link to related docs with no dead links? | 1-10 |
| Clarity | Is the doc easy to scan, understand, and act on? | 1-10 |
| Maintainability | Will this doc stay accurate as the project evolves? | 1-10 |

**Composite Score**: Average of all 5 dimensions (range 1.0-10.0).

### Step 4: Evaluate Gate Result

Present results in this format:

```text
## Documentation Quality Gate

Files assessed: [N]
Overall composite: [X.X]/10.0
Gate result: [PASS | FAIL | SKIP | OVERRIDE]

| File              | Accuracy | Completeness | Cross-Refs | Clarity | Maintain. | Composite | Status |
|-------------------|----------|--------------|------------|---------|-----------|-----------|--------|
| [file]            | [score]  | [score]      | [score]    | [score] | [score]   | [X.X]     | [P/F]  |
```

**Gate Logic**:
- **PASS**: All files have composite >= 9.0 AND no individual dimension < 8
- **FAIL**: Any file has composite < 9.0 OR any individual dimension < 8

### Step 5: Handle FAIL

If the gate FAILS:
1. List specific gaps for each failing file (which dimensions scored below threshold and why)
2. **HALT PR creation** — instruct the developer to fix the documentation gaps
3. **Override option**: If the developer explicitly requests an override, record:
   - Override justification (developer must provide a reason)
   - Override date
   - Files overridden (list of files with FAIL status)
   - If the developer has previously overridden the gate for this spec, log the override count and prior justifications
4. If overridden, proceed to Phase 2 with gate result set to OVERRIDE

### Step 6: Record Scores

Record the gate results in the spec artifacts directory at `FEATURE_DIR/doc-scores.md` for audit trail.

***

## Phase 2: Self-Review Checklist

Walk through your diff (`git diff main`) and confirm ALL of the following before creating the PR. If any item fails, fix it first.

### Security
- [ ] No API keys, tokens, credentials, or `.env` values anywhere in the diff
- [ ] No sensitive data in templates or sample data
- [ ] `.gitignore` covers any new agent-local settings or credential files

### Code Quality
- [ ] Linter passes with zero violations
- [ ] No bare exception handling — all error handling is specific
- [ ] No `# type: ignore` or `# noqa` without justification

### Tests
- [ ] Every new module/function has corresponding tests
- [ ] No tests skipped without a linked issue
- [ ] Edge cases covered: empty inputs, malformed data, missing files

### Template & SDD Integrity
- [ ] If templates changed, all required SDD fields and `[NEEDS CLARIFICATION]` markers are preserved
- [ ] Slash commands are updated together across all mirror locations

### Cross-Platform Parity
- [ ] Every new Bash script has a matching PowerShell script with identical behavior
- [ ] Shell scripts are POSIX-compatible

### Documentation
- [ ] Project documentation updated if architecture, commands, or conventions changed
- [ ] `CHANGELOG.md` updated for user-facing changes
- [ ] Documentation quality gate composite score >= 9.0 (or override recorded in Phase 1.5)

***

## Phase 3: Commit Hygiene

### Commit Message Format
Use conventional commits with the spec number as scope:

```
feat(NNN): short imperative description

- Detail of what changed
```

Allowed prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`

### Scope Rules
- Only include changes related to the spec you implemented
- Unrelated fixes go in separate PRs

***

## Phase 4: Create the Pull Request

### Target Branch
Always target `main`.

### PR Title
Use conventional commit format: `feat(NNN): short imperative description`

### PR Body
Fill out these sections:

```markdown
## Description

Implements Spec NNN: [feature name]

[2-3 sentence summary. Link to spec and related issues.]

Spec: `specs/NNN-feature-name/spec.md`

### What Changed
- [Bullet list of key changes]

## Testing

- [x] Ran existing tests
- [x] Linter passes
- [x] Markdownlint passes

## AI Disclosure

- [ ] I did **not** use AI assistance
- [x] I **did** use AI assistance (describe below)

[Name the AI agent and what it contributed.]
```

***

## Phase 5: Post-Creation Verification

After the PR is created, verify:

1. **CI passes** — all workflow checks must be green
2. **No merge conflicts** with `main`
3. **PR diff is clean** — no unintended files, debug prints, or commented-out code

If any CI check fails, push fixes immediately.

4. **Closure reminder** -- After the PR is merged, run `/spequa.16-close NNN` to formally validate and close the spec. This is Phase 8 of the SDD pipeline and is required by the constitution's Formal Closure principle.

***

**Summary: Do not create the PR until Phase 1 passes, Phase 1.5 passes (or override recorded), Phase 2 is fully checked, and Phase 3 is clean. After merge, run `/spequa.16-close` to formally close the spec.**
