---
description: Generate a test plan and test stubs from spec artifacts, ensuring 100% requirement-to-test coverage before implementation begins.
handoffs:
  - label: Implement Project
    agent: spequa.10-implement
    prompt: Start the implementation in phases
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-plan
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequirePlan
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

<!-- config-refs: test_command -->

## Project Configuration

Before executing, read `.spequa/config.yml` if it exists. If the `test_command` key is present, use it as the project's test runner command instead of inferring from the tech stack table below. If the file is missing or `test_command` is absent, fall back to framework detection from plan.md as described in step 3.

Default: `uv run pytest --tb=short -q` (Python/pytest)

If config.yml contains unrecognized keys, warn about each one and suggest the closest valid key name.

## Pipeline Position

```text
spequafy → clarify → plan → tasks → checklist → analyze → ⭐ TEST → implement → PR → merge → close
```

This command runs **after** `analyze` (needs validated artifacts) and **before** `implement` (tests must exist for TDD execution). It bridges the gap between "requirements are validated" (analyze) and "code is written" (implement).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list.
   - All file paths must be absolute.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load feature context** (all reads from FEATURE_DIR):
   - **REQUIRED**: `spec.md` — functional requirements (FR-*), acceptance criteria, success criteria, user scenarios
   - **REQUIRED**: `plan.md` — tech stack, architecture, file structure, testing strategy
   - **IF EXISTS**: `tasks.md` — implementation file paths (used for test file placement)
   - **IF EXISTS**: `data-model.md` — entities and relationships (drives model/schema tests)
   - **IF EXISTS**: `contracts/` — API specifications (drives contract/integration tests)
   - **IF EXISTS**: `checklists/` — requirements quality issues (edge cases to test)

   **If spec.md or plan.md is missing**: ERROR "Cannot generate tests without spec.md and plan.md. Run `/spequa.3-spequafy` and `/spequa.5-plan` first."

3. **Detect testing framework** from plan.md:

   Scan plan.md for tech stack references and select the appropriate testing framework:

   | Tech Stack | Primary Framework | Assertion Style | File Pattern |
   |-----------|------------------|----------------|-------------|
   | Python | `pytest` | `assert` | `test_*.py` |
   | Node.js/TypeScript | `vitest` or `jest` | `expect()` | `*.test.ts` / `*.spec.ts` |
   | Go | `testing` | `t.Error()` | `*_test.go` |
   | Java | `JUnit 5` | `assertEquals()` | `*Test.java` |
   | C# | `xUnit` / `NUnit` | `Assert.*` | `*Tests.cs` |
   | Ruby | `RSpec` | `expect().to` | `*_spec.rb` |
   | Rust | built-in `#[test]` | `assert!()` | inline `mod tests` |
   | PHP | `PHPUnit` | `$this->assert*()` | `*Test.php` |
   | Swift | `XCTest` | `XCTAssert*()` | `*Tests.swift` |
   | Shell/Bash | `bats-core` or manual | `[ ]` / `[[ ]]` | `*.bats` |

   If plan.md explicitly names a framework, use that. Otherwise infer from the tech stack table above.

   If `$ARGUMENTS` specifies a framework (e.g., "use pytest" or "vitest"), override the detection.

4. **Extract testable requirements** — Build the coverage matrix:

   For each item in spec.md, extract:

   a. **Functional Requirements** (FR-NNN):
      - Parse each `FR-*` line
      - Extract the acceptance criteria (what makes this requirement "done")
      - Classify: unit test, integration test, or end-to-end test

   b. **User Scenarios / Acceptance Criteria**:
      - Parse user stories and their acceptance scenarios
      - Each scenario maps to at least one test case
      - Happy path + error paths + edge cases

   c. **Success Criteria**:
      - Parse measurable outcomes
      - Map to performance tests, load tests, or metric-validation tests

   d. **Non-Functional Requirements** (if present):
      - Security requirements → security tests
      - Performance requirements → benchmark tests
      - Accessibility requirements → a11y tests

   e. **Data Model entities** (from data-model.md if exists):
      - Each entity → CRUD operation tests
      - Relationships → referential integrity tests
      - Validation rules → constraint tests

   f. **API Contracts** (from contracts/ if exists):
      - Each endpoint → request/response contract tests
      - Error codes → error handling tests
      - Auth requirements → authorization tests

5. **Classify tests into tiers**:

   | Tier | Type | What it tests | Run speed |
   |------|------|--------------|-----------|
   | T1 | Unit | Pure functions, models, validators | < 1s each |
   | T2 | Integration | Service interactions, DB queries, API calls | < 5s each |
   | T3 | End-to-End | User workflows, CLI commands, full stack | < 30s each |
   | T4 | Non-Functional | Performance, security, accessibility | Varies |

   **Targeting guidance**:
   - Aim for **70% T1**, **20% T2**, **10% T3/T4** distribution
   - Every FR MUST have at least one T1 or T2 test
   - Every user scenario MUST have at least one T3 test
   - Non-functional requirements covered by T4 only if measurable

6. **Generate test plan** — Write `FEATURE_DIR/tests.md`:

   ```markdown
   # Test Plan: [FEATURE NAME]

   **Generated**: [DATE]
   **Spec**: [link to spec.md]
   **Tech Stack**: [from plan.md]
   **Framework**: [detected framework]

   ## Coverage Matrix

   | Requirement | Test ID | Test Name | Tier | File |
   |------------|---------|-----------|------|------|
   | FR-001 | TST-001 | test_bootstrap_creates_submodule | T2 | tests/test_bootstrap.py |
   | FR-001 | TST-002 | test_bootstrap_fails_without_git | T1 | tests/test_bootstrap.py |
   | FR-002 | TST-003 | test_sync_updates_submodule | T2 | tests/test_sync.py |
   | US1-AC1 | TST-004 | test_user_can_bootstrap_new_project | T3 | tests/test_e2e.py |
   | SC-01 | TST-005 | test_commands_available_within_30s | T4 | tests/test_performance.py |
   | ... | ... | ... | ... | ... |

   ## Test Distribution

   | Tier | Count | Percentage | Target |
   |------|-------|-----------|--------|
   | T1 Unit | NN | NN% | 70% |
   | T2 Integration | NN | NN% | 20% |
   | T3 End-to-End | NN | NN% | 10% |
   | T4 Non-Functional | NN | NN% | — |

   ## Coverage Gaps

   [List any requirements that could not be mapped to tests, with explanation]

   ## Test Files

   [List all test files that will be generated, with brief description of what each contains]
   ```

   **Coverage rules**:
   - Every FR-NNN MUST appear at least once in the matrix
   - Every user scenario acceptance criteria MUST appear
   - If a requirement cannot be tested, document WHY in Coverage Gaps
   - No orphan tests (every test must trace to a requirement)

7. **Generate test stubs** — Create actual test files:

   For each test file in the coverage matrix:
   - Create the file at the path specified in tasks.md or plan.md's file structure
   - If no path specified, use the project's conventional test directory
   - Write complete test function stubs with:
     - Descriptive test name matching the matrix
     - Docstring linking back to the requirement (e.g., `"""Tests FR-001: Bootstrap creates submodule."""`)
     - `# TODO: Implement` marker in the body
     - Arrange/Act/Assert structure (or Given/When/Then for BDD)
     - Any obvious fixtures or setup code
   - Group related tests into logical test classes/modules

   **Stub structure example (Python/pytest)**:

   ```python
   """Tests for spequa bootstrap functionality.

   Covers: FR-001, FR-002, US1-AC1
   Spec: specs/001-shared-toolkit-sync/spec.md
   """
   import pytest


   class TestBootstrap:
       """FR-001: Developer bootstraps new project with shared toolkit."""

       def test_creates_submodule_at_spequa_path(self, tmp_path):
           """FR-001: Bootstrap creates .spequa/ submodule directory.

           Acceptance: .spequa/ exists and is a valid git submodule.
           """
           # Arrange
           # TODO: Set up a fresh git repo at tmp_path

           # Act
           # TODO: Run spequa-bootstrap.sh

           # Assert
           # TODO: Verify .spequa/ exists and is a submodule
           pytest.skip("Not yet implemented — TST-001")

       def test_fails_gracefully_outside_git_repo(self, tmp_path):
           """FR-001: Bootstrap exits with error if not in a git repo.

           Acceptance: Exit code 1, clear error message.
           """
           # Arrange
           # TODO: Use a non-git directory

           # Act
           # TODO: Run spequa-bootstrap.sh

           # Assert
           # TODO: Verify exit code 1 and error message
           pytest.skip("Not yet implemented — TST-002")
   ```

   **Stub structure example (TypeScript/vitest)**:

   ```typescript
   /**
    * Tests for user authentication.
    * Covers: FR-001, FR-002, US1-AC1
    * Spec: specs/003-user-auth/spec.md
    */
   import { describe, it, expect } from 'vitest';

   describe('FR-001: User Authentication', () => {
     it('TST-001: should create session on valid login', () => {
       // Arrange
       // TODO: Set up test user credentials

       // Act
       // TODO: Call login function

       // Assert
       // TODO: Verify session created
       expect(true).toBe(false); // Placeholder — implement TST-001
     });

     it('TST-002: should reject invalid credentials', () => {
       // Arrange
       // TODO: Set up invalid credentials

       // Act
       // TODO: Call login function

       // Assert
       // TODO: Verify rejection with appropriate error
       expect(true).toBe(false); // Placeholder — implement TST-002
     });
   });
   ```

   **Stub structure example (Bash/bats)**:

   ```bash
   #!/usr/bin/env bats
   # Tests for spequa-bootstrap.sh
   # Covers: FR-001, US1-AC1
   # Spec: specs/001-shared-toolkit-sync/spec.md

   setup() {
     TEST_DIR="$(mktemp -d)"
     cd "$TEST_DIR"
     git init
   }

   teardown() {
     rm -rf "$TEST_DIR"
   }

   @test "TST-001: bootstrap creates .spequa/ submodule" {
     # TODO: Implement
     skip "Not yet implemented — TST-001"
   }

   @test "TST-002: bootstrap fails outside git repo" {
     cd /tmp
     # TODO: Implement
     skip "Not yet implemented — TST-002"
   }
   ```

8. **Validate coverage completeness**:

   After generating all files, run a self-check:

   a. **Requirement coverage**: Count distinct FR/AC/SC IDs in tests.md vs. spec.md
      - Target: 100% of functional requirements covered
      - WARN if any FR has no test
      - ERROR if >10% of FRs are uncovered

   b. **File coverage**: Verify every test file in plan can be created at the specified path
      - WARN if test directory doesn't exist yet (will be created by implement)

   c. **Tier distribution**:
      - WARN if T1 < 50% (too few unit tests)
      - WARN if T3 > 30% (too many slow E2E tests)

   d. **Traceability check**: Every test has a requirement reference, every requirement has a test
      - Report bidirectional traceability percentage

   Display results as:

   ```text
   === Test Plan Summary ===

   Total tests:        NN
   Requirements covered: NN/NN (100%)
   Traceability:        NN% bidirectional

   Tier distribution:
     T1 Unit:          NN (NN%)
     T2 Integration:   NN (NN%)
     T3 E2E:           NN (NN%)
     T4 Non-Functional: NN (NN%)

   Files generated:     NN
   Coverage gaps:       NN (see tests.md)

   Status: PASS / WARN / FAIL
   ```

9. **Handle user input ($ARGUMENTS)**:

   The user may provide:
   - **Scope narrowing**: "only unit tests" → generate T1 only
   - **Scope expanding**: "include performance tests" → add T4 tier
   - **Framework override**: "use jest" → override detected framework
   - **File path override**: "put tests in `__tests__/`" → override test directory
   - **Focus area**: "focus on the API endpoints" → prioritize contract tests
   - **Specific requirements**: "tests for FR-003 and FR-005 only" → subset generation
   - **Regeneration**: "regenerate" or "refresh" → overwrite existing `tests.md` and stubs

10. **Report completion**:

    Output:
    - Full path to `tests.md`
    - List of generated test stub files
    - Coverage summary
    - Any coverage gaps or warnings
    - Remind user: "Run `/spequa.10-implement` to fill in the test implementations before the production code (TDD), or implement tests alongside production code."

## Anti-Patterns — What This Command Does NOT Do

- Does NOT run tests (that's the test runner's job during `/spequa.10-implement`)
- Does NOT write implementation code — only test stubs with `TODO` markers
- Does NOT generate mocks/fakes — those are implementation details for `/spequa.10-implement`
- Does NOT create performance benchmarks with actual thresholds — those come from profiling real code
- Does NOT replace manual test planning for complex integrations — use `$ARGUMENTS` to guide focus

## Integration with Other Commands

| Command | Relationship |
|---------|-------------|
| `/spequa.7-checklist` | Validates requirements *quality* → feeds edge cases to test generation |
| `/spequa.6-tasks` | Provides file paths → test stubs use the same paths |
| `/spequa.8-analyze` | Cross-checks tests.md against spec.md for drift after implementation |
| `/spequa.10-implement` | Consumes test stubs → implements tests first (TDD), then production code |
