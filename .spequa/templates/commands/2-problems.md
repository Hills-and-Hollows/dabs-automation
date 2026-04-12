---
description: Frame the problem space, constraints, and success criteria before writing the feature spec — narrows scope and surfaces risks early.
handoffs:
  - label: Create specification
    agent: spequa.3-spequafy
    prompt: Turn the problem framing into a full spec. I am building...
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Produce a concise **problem statement** artifact for the active feature: what is wrong or missing today, who is affected, constraints, and what “done” means. This step runs **after** constitution (project principles) and **before** `/spequa.3-spequafy` so the eventual spec is scoped to a well-defined problem.

## Outline

1. Detect the active feature directory (same rules as spequafy — branch `NNN-*`, `specs/NNN-*`).
2. Write or update `problems.md` in the feature directory with sections: Context, Problem, Goals, Non-goals, Risks, Open questions.
3. Cross-check against `.spequa/memory/constitution.md` for conflicts.
4. Report readiness for `/spequa.3-spequafy`.
