# Per-Section Command Overrides

Override files let you extend or replace specific phases of upstream
spequa commands without forking the entire command file. Your overrides
are preserved during upstream updates.

## Location

```text
.spequa/overrides/<command-name>/
├── phase-a-pre.md     # Insert before Phase A
├── phase-a.md         # Replace Phase A entirely
├── phase-a-post.md    # Insert after Phase A
├── phase-c-post.md    # Insert after Phase C (e.g., compliance step)
└── ...
```

## Supported Commands

| Command | Valid Phase IDs |
|---------|----------------|
| close | a, b, c, d, e |
| create-pull-request | 1, 2, 3, 4, 5 |
| diagnose | 1, 2, 3 |
| plan | 0, 1 |

## Override Types

### Insert Before (pre)

File: `.spequa/overrides/close/phase-c-pre.md`

Content is inserted immediately before Phase C begins. Use for setup
steps or prerequisite checks.

### Replace Entirely

File: `.spequa/overrides/close/phase-c.md`

Replaces the entire upstream Phase C content. Use when the default
phase logic doesn't apply to your project.

### Insert After (post)

File: `.spequa/overrides/close/phase-c-post.md`

Content is inserted immediately after Phase C completes. Use for
additional validation, compliance sign-off, or notification steps.

## Example: Adding a Compliance Step

Create `.spequa/overrides/close/phase-c-post.md`:

```markdown
### Step C4: Compliance Sign-Off

1. Present the compliance checklist to the reviewer.
2. All regulatory requirements must be verified before proceeding.
3. Record sign-off in the closure report under "Compliance Verification".
```

This content appears after Phase C (Success Criteria Verification) and
before Phase D (Visual Evidence Capture) every time `/spequa.16-close` runs.
When upstream improves Phases A, B, D, or E, those changes flow through
automatically — only your compliance step is project-local.

## Notes

- Override files contain raw markdown — no frontmatter required.
- Invalid phase references (e.g., `phase-z.md` for close) produce a
  warning and are skipped.
- Overrides are project-local and never overwritten by upstream updates.
- Multiple overrides for different phases of the same command all apply.
