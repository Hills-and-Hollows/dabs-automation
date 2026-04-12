# PR Gate Status

**Created**: 2026-04-12
**Workflow**: `.github/workflows/pr-gate.yml`

The PR gate was introduced via `chore/pr-gate-upgrade`. Most jobs start in "soft" mode (`continue-on-error: true`) because dabs-automation had no linting, formatting, or type-checking enforcement before this, and flipping everything to blocking in one PR would fail every future PR until a multi-week cleanup lands.

## Current gate jobs

| Job | Blocking? | Notes |
|---|---|---|
| `format` (black --check) | No (soft) | Promote to blocking after `black src tests` has been run once on main. |
| `lint` (pylint) | No (soft — uses `--exit-zero`) | Establish a baseline score, then set a minimum threshold. pylint is too noisy to block on without configuration. |
| `typecheck` (mypy) | No (soft) | Needs a `mypy.ini` or `[tool.mypy]` in a pyproject.toml to scope what gets checked and ignore third-party untyped modules. |
| `pytest` (unit + non-integration) | No (soft) | Runs pytest excluding `integration`, `performance`, `slow` markers. Should quickly become blocking once it has a clean baseline. |
| `docker-build` (Dockerfile.railway) | **Yes** | A failing Docker build means production deploy is broken. This is the only hard gate at launch. |
| `mcp-tests.yml` (existing) | Yes | Runs `tests/integration/test_dabs_mcp_tools.py`. Unchanged by this PR. |

## Promotion plan

Promote each soft job to blocking once:

1. The job has run on main for 3 consecutive green builds, OR
2. The underlying tool's output has been reviewed and any baseline issues fixed on main.

When promoting, remove `continue-on-error: true` from the job in `.github/workflows/pr-gate.yml` and update this document.

## Out of scope for the initial gate

- **Integration tests** (pytest `-m integration`) — require external services (QBO OAuth, Mercury, SSCS). They run in `mcp-tests.yml` for the MCP-only slice. Broader integration test execution in CI is a separate spec.
- **Performance tests** — require stable baselines and are intentionally excluded from the fast PR gate.
- **Netlify frontend build validation** — currently the `auto-update-dabs-catalog.yml` workflow builds the Vite frontend. A dedicated frontend PR job can be added when the frontend has its own tests.
- **Coverage thresholds** — should be added once the pytest baseline is green.

## Related

- `.github/workflows/pr-gate.yml` — the workflow
- `.github/workflows/mcp-tests.yml` — the existing (unchanged) MCP integration test workflow
- `.github/dependabot.yml` — weekly updates for pip, docker, github-actions, npm
- `requirements.txt` — already pins black 23.11.0, pylint 3.0.2, mypy 1.7.1, pytest 7.4.3
