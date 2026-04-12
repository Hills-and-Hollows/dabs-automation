#!/usr/bin/env bash

# Concurrency lock management for SDD pipeline runs
#
# Checks .pipeline-state.json for active locks to prevent two
# pipeline runs from executing simultaneously against the same repo.
#
# Usage: ./check-concurrent-runs.sh [--json] [--status] [--feature-dir <path>]
#
# Flags:
#   --json         Output JSON (default is JSON anyway, reserved for future formats)
#   --status       Report lock status without acquiring/clearing stale locks
#   --feature-dir  Override auto-detection of feature directory
#
# Exit codes:
#   0 = no conflict (safe to proceed)
#   1 = locked (active pipeline run in progress)

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

# --- Parse arguments ---
JSON_OUTPUT=false
STATUS_ONLY=false
FEATURE_DIR_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        --feature-dir)
            FEATURE_DIR_OVERRIDE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

# --- Resolve feature directory ---
if [[ -n "$FEATURE_DIR_OVERRIDE" ]]; then
    FEATURE_DIR="$FEATURE_DIR_OVERRIDE"
else
    REPO_ROOT=$(get_repo_root)
    CURRENT_BRANCH=$(get_current_branch)
    FEATURE_DIR=$(find_feature_dir_by_prefix "$REPO_ROOT" "$CURRENT_BRANCH")
fi

# Normalize to absolute path
if [[ ! "$FEATURE_DIR" = /* ]]; then
    FEATURE_DIR="$(cd "$FEATURE_DIR" 2>/dev/null && pwd)" || {
        echo '{"locked":false,"message":"Feature directory not found"}'
        exit 0
    }
fi

STATE_FILE="$FEATURE_DIR/.pipeline-state.json"

# --- Check if state file exists ---
if [[ ! -f "$STATE_FILE" ]]; then
    echo '{"locked":false,"message":"No pipeline state found"}'
    exit 0
fi

# --- Read lock fields from state file ---
# Use jq if available, fall back to grep/sed
read_json_field() {
    local file="$1"
    local field="$2"

    if command -v jq >/dev/null 2>&1; then
        jq -r "$field // empty" "$file" 2>/dev/null || echo ""
    else
        # Fallback: simple grep/sed extraction (handles flat JSON)
        grep -o "\"$(echo "$field" | sed 's/\./":"[^"]*".*"/; s/\./"[^"]*","/g')" "$file" 2>/dev/null | head -1 | sed 's/.*: *"\{0,1\}\([^",}]*\)"\{0,1\}.*/\1/' || echo ""
    fi
}

if command -v jq >/dev/null 2>&1; then
    LOCK_PID=$(jq -r '.lock.pid // empty' "$STATE_FILE" 2>/dev/null || echo "")
    LOCK_ACQUIRED=$(jq -r '.lock.acquired_at // empty' "$STATE_FILE" 2>/dev/null || echo "")
else
    # Fallback: extract lock.pid with sed
    LOCK_PID=$(sed -n 's/.*"pid"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p' "$STATE_FILE" | head -1)
    LOCK_ACQUIRED=$(sed -n 's/.*"acquired_at"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$STATE_FILE" | head -1)
fi

# --- No lock set ---
if [[ -z "$LOCK_PID" || "$LOCK_PID" == "null" ]]; then
    echo '{"locked":false,"message":"No active lock"}'
    exit 0
fi

# --- Lock exists: check if PID is alive ---
if kill -0 "$LOCK_PID" 2>/dev/null; then
    # Process is alive - pipeline run in progress
    cat <<EOF
{"locked":true,"pid":${LOCK_PID},"acquired_at":"${LOCK_ACQUIRED}","message":"Pipeline run in progress"}
EOF
    exit 1
else
    # Process is dead - stale lock
    if [[ "$STATUS_ONLY" == "false" ]]; then
        # Clear the stale lock by writing null to lock fields
        if command -v jq >/dev/null 2>&1; then
            tmp_file="${STATE_FILE}.tmp"
            jq '.lock.pid = null | .lock.acquired_at = null' "$STATE_FILE" > "$tmp_file" && mv "$tmp_file" "$STATE_FILE"
        else
            # Fallback: use sed to null out the pid and acquired_at
            sed -i.bak \
                -e 's/"pid"[[:space:]]*:[[:space:]]*[0-9]*/"pid": null/' \
                -e 's/"acquired_at"[[:space:]]*:[[:space:]]*"[^"]*"/"acquired_at": null/' \
                "$STATE_FILE"
            rm -f "${STATE_FILE}.bak"
        fi
    fi

    cat <<EOF
{"locked":false,"stale":true,"old_pid":${LOCK_PID},"message":"Stale lock cleared"}
EOF
    exit 0
fi
