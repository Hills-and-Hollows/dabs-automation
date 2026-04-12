#!/usr/bin/env bash
# spequa-bootstrap.sh — Add spequa as a submodule and create symlinks
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/spequa-common.sh"

# Defaults
REMOTE="https://github.com/EQUAStart/spequa.git"
BRANCH="main"
SUBMODULE_PATH=".spequa"
FORCE=false
AGENTS_ARG=""

usage() {
    cat <<'EOF'
Usage: spequa-bootstrap.sh [OPTIONS]

Add spequa as a git submodule and create symlinks for SDD toolkit.

Options:
  --remote URL      Remote URL for spequa
                    (default: https://github.com/EQUAStart/spequa.git)
  --branch BRANCH   Tracking branch (default: main)
  --path PATH       Submodule mount path (default: .spequa)
  --agents LIST     Comma-separated agent keys to enable (e.g. claude,cursor-agent,agy)
                    Only these agents will get symlinks. Omit to auto-detect.
  --force           Re-bootstrap even if submodule exists
  --help            Show this help message

Agent keys: claude, cursor-agent, agy, copilot, gemini, codex, windsurf, amp,
  kilocode, roo, kiro-cli, qwen, opencode, auggie, codebuddy, qodercli, shai, bob, comet

Exit codes:
  0 — Success
  1 — Not a git repository
  2 — Submodule already exists (without --force)
  3 — Remote unreachable
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --remote) REMOTE="$2"; shift 2 ;;
        --branch) BRANCH="$2"; shift 2 ;;
        --path) SUBMODULE_PATH="$2"; shift 2 ;;
        --agents) AGENTS_ARG="$2"; shift 2 ;;
        --force) FORCE=true; shift ;;
        --help) usage; exit 0 ;;
        *) spequa_error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# Preconditions
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    spequa_error "Not a git repository. Run 'git init' first."
    exit 1
fi

if [[ -d "$SUBMODULE_PATH" ]] && [[ "$FORCE" != true ]]; then
    spequa_error "Submodule already exists at '$SUBMODULE_PATH'. Use --force to re-bootstrap."
    exit 2
fi

# If --force and submodule exists, remove it first
if [[ -d "$SUBMODULE_PATH" ]] && [[ "$FORCE" == true ]]; then
    spequa_info "Removing existing submodule at '$SUBMODULE_PATH'..."
    git submodule deinit -f "$SUBMODULE_PATH" 2>/dev/null || true
    git rm -f "$SUBMODULE_PATH" 2>/dev/null || true
    rm -rf ".git/modules/$SUBMODULE_PATH" 2>/dev/null || true
fi

# Add submodule
spequa_info "Adding submodule from $REMOTE at $SUBMODULE_PATH (branch: $BRANCH)..."
if ! git submodule add -b "$BRANCH" "$REMOTE" "$SUBMODULE_PATH" 2>&1; then
    spequa_error "Failed to add submodule. Is the remote accessible?"
    exit 3
fi

git submodule update --init "$SUBMODULE_PATH"

# Build agents list
agents_json=""
if [[ -n "$AGENTS_ARG" ]]; then
    # User specified agents explicitly — validate and build JSON
    agents_json="["
    first=true
    IFS=',' read -r -a agent_list <<< "$AGENTS_ARG"
    for key in "${agent_list[@]}"; do
        key="$(echo "$key" | tr -d ' ')"
        folder="$(spequa_key_to_folder "$key")"
        if [[ -z "$folder" ]]; then
            spequa_warn "Unknown agent key: $key (skipping)"
            continue
        fi
        $first || agents_json="$agents_json, "
        agents_json="$agents_json\"$key\""
        first=false
    done
    agents_json="$agents_json]"
    spequa_info "Agents (from --agents): $agents_json"
else
    # Auto-detect: check which agent dirs already exist in the project
    detected=""
    for key in $EQUASPEC_ALL_AGENT_KEYS; do
        folder="$(spequa_key_to_folder "$key")"
        if [[ -d "$folder" ]]; then
            detected="$detected $key"
        fi
    done

    # Always include claude (primary agent)
    case " $detected " in
        *" claude "*) ;;
        *) detected="$detected claude" ;;
    esac

    # Sort and build JSON
    sorted="$(echo "$detected" | tr ' ' '\n' | grep -v '^$' | sort | tr '\n' ' ')"
    agents_json="["
    first=true
    for key in $sorted; do
        $first || agents_json="$agents_json, "
        agents_json="$agents_json\"$key\""
        first=false
    done
    agents_json="$agents_json]"
    spequa_info "Agents (auto-detected): $agents_json"
fi

# Initialize .spequa.json
spequa_info "Initializing .spequa.json..."
spequa_json_write ".spequa.json" "false" "" "" "$agents_json"

# Create symlinks (filtered by agents list)
spequa_info "Creating symlinks..."
"$SCRIPT_DIR/spequa-link.sh" --verbose

spequa_info "Bootstrap complete."
