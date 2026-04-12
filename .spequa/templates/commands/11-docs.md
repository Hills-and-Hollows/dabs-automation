---
description: Validate documentation structural integrity, cross-references, audience boundaries, and command drift before PR creation.
handoffs:
  - label: Create Pull Request
    agent: spequa.14-create-pull-request
  - label: Score Documentation Quality
    agent: spequa.12-score-docs
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Structurally validate all project documentation — broken links, stale references, missing coverage, audience boundary violations, and command drift — producing a categorized report with severity levels. This command complements the Doc Quality Gate (score-docs rubric) by checking structural correctness before quality scoring runs.

## Execution Steps

### 1. Load Documentation Manifest

Read `.spequa/docs-manifest.yml` from the repository root. If the file does not exist, report an error and instruct the user to create it (see `specs/007-docs-validation-gate/data-model.md` for the schema).

Parse three sections:

- `documentable[]` — path patterns and their expected doc coverage targets
- `audience_boundary` — `user_docs` glob patterns and `forbidden_terms` list
- `command_drift` — dev prefix, template dir, and `intentional_asymmetry` lists

### 2. Identify Documentation Files

Collect the full set of documentation files to validate. Always validate ALL docs regardless of which files were modified in the current branch — code changes may invalidate existing documentation.

**Files to scan:**

- All `.md` files in `docs/` (expand `docs/*.md`)
- `README.md` (repository root)
- `CHANGELOG.md` (repository root, if exists)

**Files excluded from validation:**

- `specs/` directories (feature-scoped artifacts, not core docs)
- `extensions/` directories (excluded per CI convention)
- Agent command directories (`.claude/commands/`, `.cursor/commands/`, etc.)
- Template command files (`templates/commands/`)

### 3. Check: Broken Links (CRITICAL)

For each documentation file identified in step 2:

1. Scan for all markdown links matching the pattern `[text](path)` — extract the link target `path`.
2. Skip external links (starting with `http://`, `https://`, `mailto:`).
3. Skip anchor-only links (starting with `#`).
4. For relative links, resolve the path relative to the file's directory.
5. Check if the resolved path exists in the current branch's filesystem.
6. For links with anchors (e.g., `file.md#section`), verify the file exists (anchor validation is optional).

**Report format for each broken link:**

```text
CRITICAL: [file_path:line_number] Broken link — target 'target_path' does not exist
  Fix: Update the link to point to the correct file, or remove if the target was intentionally deleted.
```

### 4. Check: Stale References (CRITICAL)

For each documentation file identified in step 2:

1. Scan for inline code references — backtick-wrapped strings that look like file paths (containing `/` or `.` with a file extension).
   - Match patterns like `` `scripts/bash/spequa-bootstrap.sh` ``, `` `src/spequafy_cli/__init__.py` ``, `` `.spequa/config.yml` ``
2. For each referenced path, check if it exists in the current branch's filesystem.
3. Also scan for backtick-wrapped CLI flags (e.g., `` `--force` ``, `` `--dry-run` ``).
   - For flags, verify they exist in the corresponding script's content (search for the flag string in scripts matching the context).
4. Skip references that are clearly example/placeholder content (inside code blocks with language markers).

**Report format for each stale reference:**

```text
CRITICAL: [file_path:line_number] Stale reference — 'referenced_path' does not exist in codebase
  Fix: Update the reference to the current path, or remove if the artifact was deleted.
```

### 5. Check: Missing Documentation Coverage (WARNING)

Using the `documentable[]` entries from the manifest:

1. For each entry, expand the `pattern` glob against the current codebase.
2. For each matched file, check if it is referenced (by filename or path) in at least one of the entry's `docs[]` target files.
3. A "reference" means the filename or a recognizable portion of the path appears as text in the target doc file.

**Report format for each uncovered file:**

```text
WARNING: Missing coverage — 'matched_file' (description) is not referenced in any of: [doc_targets]
  Fix: Add a reference to this file in one of the listed documentation targets.
```

### 6. Check: Audience Boundary Violations (CRITICAL)

Using the `audience_boundary` section from the manifest:

1. Expand `user_docs` glob patterns to get the list of user-facing documentation files.
2. For each user-facing doc file, scan every line for each `forbidden_terms` entry.
3. Match is case-sensitive substring search.
4. Skip matches inside YAML frontmatter (between `---` markers at the top of the file).
5. Skip matches inside HTML comments (`<!-- ... -->`).

**Report format for each violation:**

```text
CRITICAL: [file_path:line_number] Audience boundary violation — forbidden term 'term' found in user-facing doc
  Fix: Remove or rewrite this content. Dev-internal details belong in CLAUDE.md, not in user-facing documentation.
```

### 7. Check: Command Drift (WARNING/INFO)

Using the `command_drift` section from the manifest:

1. List all dev commands matching `{dev_prefix}*.md` (e.g., `.claude/commands/spequa.*.md`).
2. For each dev command, derive the template counterpart by stripping the prefix (e.g., `spequa.5-plan.md` → `templates/commands/plan.md`).
3. Check for intentional asymmetry:
   - If the command name (without extension) is in `intentional_asymmetry.dev_only`, report as INFO and skip drift check.
   - If a template command name is in `intentional_asymmetry.template_only`, report as INFO and skip drift check.
4. For each matched pair, compare body content:
   - Read both files.
   - Strip frontmatter from both (everything between the first two `---` lines, inclusive).
   - Normalize whitespace (collapse multiple blank lines, trim trailing whitespace).
   - If the normalized bodies differ, report as WARNING with a brief summary of what changed (first divergent section heading or first 50 characters of difference).

**Report format for drift:**

```text
WARNING: Command drift — 'command_name' dev and template bodies differ
  Dev: .claude/commands/spequa.command_name.md
  Template: templates/commands/command_name.md
  Difference: [brief summary of first divergence]
  Fix: Sync the body content between both files. Frontmatter differences (handoffs, scripts) are expected.
```

**Report format for intentional asymmetry:**

```text
INFO: Intentional asymmetry — 'command_name' exists only in [dev|template] set (reason from manifest comments)
```

### 8. Produce Validation Report

Compile all findings into a structured report:

```markdown
# Documentation Validation Report

**Date**: [current date] | **Branch**: [current branch name]

## Summary
| Category           | Critical | Warning | Info |
|--------------------|----------|---------|------|
| Broken Links       | N        | —       | —    |
| Stale References   | N        | —       | —    |
| Missing Coverage   | —        | N       | —    |
| Command Drift      | —        | N       | N    |
| Audience Boundary  | N        | —       | N    |
| **Total**          | **N**    | **N**   | **N**|

## Critical Issues (blocks PR)
[List each CRITICAL finding with file:line, description, and fix guidance]

## Warnings (should fix)
[List each WARNING finding]

## Info (awareness)
[List each INFO finding]

## Result: PASS | FAIL (N critical issues)
```

**Result determination:**

- **PASS**: Zero CRITICAL issues. Warnings and info items are reported but do not block.
- **FAIL**: One or more CRITICAL issues found. PR creation should be blocked until resolved.

### 9. Output

Display the full validation report to the user. Do NOT write it to a file — this is a live validation check, not a persisted artifact.

If invoked as part of `/spequa.14-create-pull-request`, return the result (PASS/FAIL) to the calling command for gate enforcement.

## Behavior Rules

- **Always validate ALL docs**, not just changed files. Code changes may invalidate existing documentation.
- **Never modify any files**. This command is read-only — it reports issues for the developer to fix.
- **Be precise with line numbers**. Every finding must include the exact file path and line number.
- **Distinguish severity clearly**. CRITICAL = blocks PR. WARNING = should fix. INFO = awareness only.
- **Skip spec artifacts**. Files in `specs/` directories are feature-scoped and not subject to core doc validation.
- **Respect frontmatter**. Do not flag terms found inside YAML frontmatter or HTML comments.
- If the manifest file is missing, report an error and stop — do not attempt validation without the manifest.
