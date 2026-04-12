---
description: "14-gate PR code review checklist calibrated to the Spequa codebase. Run before merge on every PR."
handoffs:
  - label: Create Pull Request
    agent: spequa.14-create-pull-request
  - label: Comet Review
    agent: spequa.15-comet-review
---

# Spequa — PR Code Review Checklist (14/14)

Based on the Spequa codebase — a Python 3.11+ CLI + MCP server (Typer/Rich/FastMCP) with cross-platform scripting, 18-agent command distribution, an extension system, and SDD template infrastructure, linted by Ruff + markdownlint and tested via pytest across Python 3.11/3.12/3.13.

## Target PR

```text
$ARGUMENTS
```

If a PR URL or number is provided, fetch context with `gh pr view`. Otherwise review the current branch diff against `main`.

---

## Gate 1: Security & Secrets Exposure

- [ ] No API keys, tokens, credentials, or `.env` values hardcoded in code — especially in MCP server tools (`src/spequa_mcp/`), CLI commands, or scripts
- [ ] `.gitignore` covers all agent-local settings, credentials, and virtual environments (`.venv/`, `.spequa.json` secrets, agent config files)
- [ ] CodeQL security scanning (`codeql.yml`) not broken by changes — both `actions` and `python` language analyzers still functional
- [ ] No sensitive data embedded in template files (`templates/`), sample data (`sample-data/`), or extension manifests (`extensions/`)
- [ ] Cross-platform scripts (`scripts/bash/`, `scripts/powershell/`) do not leak environment variables, paths, or system info in output

## Gate 2: Python Code Quality & Ruff Compliance

- [ ] `uvx ruff check src/` passes cleanly — zero lint violations in `src/spequafy_cli/` and `src/spequa_mcp/`
- [ ] No bare `except:` or `except Exception` without proper handling — all errors caught with specificity
- [ ] Type hints used consistently on all new public functions and CLI command signatures (Typer requires typed params)
- [ ] No `# type: ignore` or `# noqa` suppressions without a justifying inline comment
- [ ] Imports organized per Ruff/isort rules — stdlib, third-party (typer, rich, httpx, fastmcp), local — no circular imports between `spequafy_cli` and `spequa_mcp`

## Gate 3: Test Coverage & Pytest Integrity

- [ ] New logic in `src/` has corresponding tests in `tests/` — CLI commands, MCP tools, domain analysis, and template rendering all covered
- [ ] `uv run pytest` passes across the full Python matrix (3.11, 3.12, 3.13) — no version-specific failures
- [ ] No tests skipped (`@pytest.mark.skip`) without a linked issue or TODO explaining when they'll be re-enabled
- [ ] Edge cases covered: empty inputs, malformed data files, missing templates, invalid YAML/JSON in `sample-data/`
- [ ] Test fixtures don't depend on filesystem state outside the test directory — no hardcoded paths to user home or system dirs

## Gate 4: Template System & SDD Compliance

- [ ] Changes to master templates in `templates/` (spec, plan, tasks, checklist, constitution) preserve all required SDD fields and `[NEEDS CLARIFICATION]` markers
- [ ] Constitution Articles (I-IX) not violated — verify specific articles:
  - Article III (Test-First): baseline captured, tests before implementation
  - Article IV (Cross-Platform): Bash + PowerShell parity
  - Article V (Multi-Agent): all 18 dirs updated (see Gate 11)
  - Article VI (Formal Closure): closure artifacts present if spec merged
  - Article VII (Doc Quality): scores meet threshold (see Gate 12)
  - Article IX (Simplicity): no premature abstractions, complexity justified
- [ ] Slash command definitions in `templates/commands/` and `.claude/commands/` are consistent and updated together
- [ ] Template rendering logic handles missing optional fields gracefully — no `KeyError` or `None` injection into output
- [ ] New templates include proper Markdown structure that passes markdownlint

## Gate 5: Cross-Platform Script Parity

- [ ] Every new or modified Bash script in `scripts/bash/` has a corresponding PowerShell script in `scripts/powershell/` with identical behavior
- [ ] Shell scripts are POSIX-compatible (no bashisms like `[[`, `source`, arrays) unless explicitly documented
- [ ] Scripts handle missing dependencies gracefully (`uv`, `git`, `python3`, AI agent CLIs) with clear error messages
- [ ] File path handling works on Windows (backslashes), macOS, and Linux — no hardcoded `/` separators in Python code that touches the filesystem
- [ ] Script permissions (`chmod +x`) set correctly and `.gitattributes` configured for line-ending handling
- [ ] Mirror scripts in `.spequa/scripts/` stay in sync with `scripts/`

## Gate 6: Extension System & Plugin Integrity

- [ ] Extension manifest schema (`extensions/`) changes are backward-compatible — existing extensions must still validate
- [ ] Extension catalog (official + community) entries include required fields: name, version, description, compatibility
- [ ] New extensions don't conflict with existing ones — namespace collisions checked in catalog
- [ ] Extension loading/discovery code handles malformed manifests, missing files, and version mismatches without crashing
- [ ] Extensions excluded from markdownlint (`!extensions/**/*.md` in lint config) — verify exclusion still correct

## Gate 7: MCP Server & CLI Interface Safety

- [ ] MCP server tools in `src/spequa_mcp/` properly validate input parameters — no arbitrary file access or command injection via tool arguments
- [ ] CLI commands (`src/spequafy_cli/`) return proper exit codes (0 success, 1 error) — no silent failures
- [ ] New CLI subcommands registered in `__init__.py:main()` entry point and visible in `--help` output
- [ ] MCP tool responses are structured JSON — no raw strings or unhandled exceptions leaking to the client
- [ ] `spequafy init` flow still works end-to-end after changes — template bootstrapping, AI agent detection, config generation all functional

## Gate 8: CI/CD & Workflow Integrity

- [ ] No changes to `test.yml`, `lint.yml`, `codeql.yml`, `docs.yml`, `release.yml`, or `release-trigger.yml` without verifying all jobs still pass
- [ ] GitHub Actions versions pinned to specific major versions (`@v6`, `@v7`) — no floating `@latest` or `@main` refs
- [ ] Dependabot configuration (`dependabot.yml`) still covers pip and github-actions ecosystems
- [ ] Workflow permissions follow least-privilege: `contents: read` by default, `security-events: write` only for CodeQL
- [ ] CODEOWNERS (`* @ShawnOwen`) not circumvented — no new paths added that bypass required review

## Gate 9: Documentation & Markdown Quality

- [ ] `npx markdownlint-cli2 '**/*.md' '!extensions/**/*.md'` passes — no heading style, line-length, or whitespace violations
- [ ] `CLAUDE.md` updated if architecture, build commands, test commands, or key conventions change
- [ ] `AGENTS.md` updated if new AI agent configurations are added or existing ones modified
- [ ] `CHANGELOG.md` updated for user-facing changes following existing format (version, date, category)
- [ ] `docs/` directory content (quickstart, installation, pipeline) stays in sync with actual CLI behavior and project structure
- [ ] Audience boundary respected: no dev-internal content (CLAUDE.md references, contributor workflows, module paths) leaking into user-facing docs (`docs/*.md`, `README.md`)

## Gate 10: Spec Compliance & PR Hygiene

- [ ] PR references the relevant spec from `specs/NNN-feature-name/` directory (e.g., "Implements Spec 012") and links any corresponding GitHub issue
- [ ] Commit messages follow conventional commits format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, with optional scope like `feat(012):`
- [ ] PR template checklist completed: tested locally with `uv run spequafy --help`, ran `uv sync && uv run pytest`, tested with sample project if applicable
- [ ] AI Disclosure section in PR template filled out honestly — AI-assisted vs. human-authored clearly indicated
- [ ] No unrelated changes bundled — PR scope matches the spec/issue being addressed; dependency bumps (`chore(deps):`) kept in separate PRs

## Gate 11: Multi-Agent Distribution Parity

- [ ] All 18 agent directories contain identical command sets (Constitution Article V):
  `.agent/workflows/`, `.agents/commands/`, `.augment/commands/`, `.bob/commands/`, `.claude/commands/`, `.codebuddy/commands/`, `.codex/prompts/`, `.cursor/commands/`, `.gemini/commands/`, `.github/agents/`, `.kilocode/workflows/`, `.kiro/prompts/`, `.opencode/command/`, `.qoder/commands/`, `.qwen/commands/`, `.roo/commands/`, `.shai/commands/`, `.windsurf/workflows/`
- [ ] New commands added to `_command_install.py` `SPEQUA_COMMAND_ORDER` registry with correct integer or decimal order
- [ ] New commands added to `templates/commands/` (unnumbered canonical) AND all 18 agent dirs (numbered `spequa.N-stem.md`)
- [ ] `.spequa/templates/commands/` mirror stays in sync with `templates/commands/`
- [ ] Command drift between dev commands (`.claude/commands/spequa.*.md`) and template commands (`templates/commands/*.md`) is documented or resolved — run `/spequa.11-docs` to verify

## Gate 12: Pipeline Gate Verification

- [ ] `/spequa.11-docs` ran and PASSED (zero CRITICAL issues) — or failures fixed before PR creation
- [ ] `/spequa.12-score-docs` ran on all modified doc files — composite score >= 9.0, no individual dimension < 8.0
- [ ] If doc quality gate was overridden, justification is recorded in `specs/NNN-feature/doc-scores.md`
- [ ] PR description includes gate results: `Docs Validation: PASS` and `Doc Quality: PASS (X.X/10.0)`
- [ ] Baseline test snapshot exists at `specs/NNN-feature/baseline-tests.md` — final test count shows no regressions vs baseline

## Gate 13: Spec Traceability & Closure Readiness

- [ ] All tasks in `specs/NNN-feature/tasks.md` marked `[X]` (complete) — no open tasks at merge time
- [ ] All success criteria (`SC-NNN`) in `spec.md` have verification evidence (test output, screenshot, or manual confirmation)
- [ ] All functional requirements (`FR-NNN`) traced to at least one completed task in `tasks.md`
- [ ] `spec.md` status field updated from `Draft` to `Complete` with closure date
- [ ] `closure-report.md` exists and is well-formed (uses `templates/closure-report-template.md` structure)
- [ ] `evidence/demo-steps.md` documents verification steps — or text-only evidence provided when browser automation unavailable
- [ ] No `[NEEDS CLARIFICATION]` markers remaining in `spec.md` or `plan.md`

## Gate 14: CI Check Gate

- [ ] All required CI checks pass on the PR before merge:
  - `Test & Lint Python` -> ruff job + pytest job (3.11, 3.12, 3.13)
  - `Lint` -> markdownlint job
  - `CodeQL` -> security analysis (actions + python)
- [ ] No merge conflicts with `main`
- [ ] CODEOWNERS auto-requested — `@ShawnOwen` appears as requested reviewer
- [ ] PR diff is clean — no unintended files, no debug prints, no commented-out code
- [ ] If any CI check failed and was fixed, the fix is in a new commit (not amend) on the same branch

---

## Verdict

After completing all 14 gates, assign one of:

| Verdict | Criteria |
|---------|----------|
| **APPROVED** | All 14 gates pass (all checkboxes checked) |
| **CHANGES_REQUIRED** | Any gate has unchecked items — list failing gates and specific items |
| **INCONCLUSIVE** | Review could not be completed (e.g., CI still running, missing artifacts) |

Report format:

```text
VERDICT: [APPROVED | CHANGES_REQUIRED | INCONCLUSIVE]
GATES_PASSED: [N]/14
FAILING_GATES: [list of gate numbers and failing items]
```
