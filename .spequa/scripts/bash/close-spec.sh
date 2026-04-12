#!/usr/bin/env bash

# Close spec helper script
#
# Locates a spec directory by number, verifies the implementing PR is merged,
# and outputs JSON with paths and merge metadata for the closure workflow.
#
# Usage: ./close-spec.sh [OPTIONS] <spec-number>
#
# OPTIONS:
#   --json              Output in JSON format
#   --help, -h          Show help message
#
# ARGUMENTS:
#   <spec-number>       Spec number (e.g., 005) or full directory name (e.g., 005-spec-closure)
#
# OUTPUTS:
#   JSON mode: SPEC_DIR, SPEC_FILE, SPEC_NAME, PR_URL, MERGE_DATE, BASELINE_FILE, PR_MERGED,
#              MERGE_COMMIT (merge SHA on base branch, empty if unknown), DEFAULT_BRANCH
#   Text mode: Key: value pairs

set -e

# Parse command line arguments
JSON_MODE=false
SPEC_INPUT=""

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: close-spec.sh [OPTIONS] <spec-number>

Locate a spec directory and verify its implementing PR is merged.

OPTIONS:
  --json              Output in JSON format
  --help, -h          Show this help message

ARGUMENTS:
  <spec-number>       Spec number (e.g., 005) or full name (e.g., 005-spec-closure)

EXAMPLES:
  # Close spec 004
  ./close-spec.sh --json 005

  # Close by full name
  ./close-spec.sh --json 005-spec-closure

EOF
            exit 0
            ;;
        *)
            # Treat as spec number/name if not a flag
            if [[ -z "$SPEC_INPUT" ]]; then
                SPEC_INPUT="$arg"
            fi
            ;;
    esac
done

# Validate spec input
if [[ -z "$SPEC_INPUT" ]]; then
    echo "ERROR: Spec number or name is required." >&2
    echo "Usage: close-spec.sh [--json] <spec-number>" >&2
    exit 1
fi

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get repository root
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/specs"

# Default branch (for closure report + git diff; prefer gh, else origin/HEAD, else main)
DEFAULT_BRANCH="main"
if command -v gh >/dev/null 2>&1; then
    DB=$(cd "$REPO_ROOT" && gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "")
    if [[ -n "$DB" ]]; then
        DEFAULT_BRANCH="$DB"
    fi
else
    ORIG=$(git -C "$REPO_ROOT" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "")
    if [[ -n "$ORIG" ]]; then
        DEFAULT_BRANCH="$ORIG"
    fi
fi

# Extract numeric prefix from input (handle both "005" and "005-feature-name")
if [[ "$SPEC_INPUT" =~ ^([0-9]{3}) ]]; then
    PREFIX="${BASH_REMATCH[1]}"
else
    echo "ERROR: Invalid spec identifier '$SPEC_INPUT'. Expected format: NNN or NNN-feature-name" >&2
    exit 1
fi

# Find the spec directory by prefix
SPEC_DIR=""
MATCH_COUNT=0

if [[ -d "$SPECS_DIR" ]]; then
    for dir in "$SPECS_DIR"/"$PREFIX"-*; do
        if [[ -d "$dir" ]]; then
            SPEC_DIR="$dir"
            MATCH_COUNT=$((MATCH_COUNT + 1))
        fi
    done
fi

if [[ $MATCH_COUNT -eq 0 ]]; then
    echo "ERROR: No spec directory found with prefix '$PREFIX' in $SPECS_DIR" >&2
    exit 1
fi

if [[ $MATCH_COUNT -gt 1 ]]; then
    echo "ERROR: Multiple spec directories found with prefix '$PREFIX'. Please use the full name." >&2
    exit 1
fi

# Validate spec.md exists
SPEC_FILE="$SPEC_DIR/spec.md"
if [[ ! -f "$SPEC_FILE" ]]; then
    echo "ERROR: spec.md not found in $SPEC_DIR" >&2
    exit 1
fi

# Check for baseline-tests.md
BASELINE_FILE="$SPEC_DIR/baseline-tests.md"
if [[ ! -f "$BASELINE_FILE" ]]; then
    BASELINE_FILE=""
fi

# Check PR merge status via gh CLI (if available)
PR_URL=""
MERGE_DATE=""
PR_MERGED=false

SPEC_NAME=$(basename "$SPEC_DIR")

if command -v gh >/dev/null 2>&1; then
    # Search for merged PRs matching the spec number
    PR_DATA=$(gh pr list --state merged --search "$PREFIX" --json url,mergedAt --limit 5 2>/dev/null || echo "[]")

    if [[ "$PR_DATA" != "[]" && -n "$PR_DATA" ]]; then
        # Try to find a PR that matches this spec
        PR_URL=$(echo "$PR_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data:
    print(data[0].get('url', ''))
" 2>/dev/null || echo "")

        MERGE_DATE=$(echo "$PR_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data:
    print(data[0].get('mergedAt', '')[:10])
" 2>/dev/null || echo "")

        if [[ -n "$PR_URL" ]]; then
            PR_MERGED=true
        fi
    fi
fi

# Merge commit on base branch (requires gh + real PR URL)
MERGE_COMMIT=""
if command -v gh >/dev/null 2>&1 && [[ -n "$PR_URL" && "$PR_URL" == http* ]]; then
    MERGE_COMMIT=$(gh pr view "$PR_URL" --json mergeCommit --jq '.mergeCommit.oid' 2>/dev/null || echo "")
fi

# If gh is not available or no PR found, check git log for merge evidence
if ! $PR_MERGED; then
    if git log --oneline main 2>/dev/null | grep -qi "$PREFIX"; then
        PR_MERGED=true
        MERGE_DATE=$(date +%Y-%m-%d)
        PR_URL="(detected via git log, no gh CLI PR match)"
    fi
fi

# Output results
if $JSON_MODE; then
    # Escape paths for JSON (PR_MERGED as JSON boolean)
    if $PR_MERGED; then
        PR_MERGED_JSON="true"
    else
        PR_MERGED_JSON="false"
    fi
    printf '{"SPEC_DIR":"%s","SPEC_FILE":"%s","SPEC_NAME":"%s","PR_URL":"%s","MERGE_DATE":"%s","BASELINE_FILE":"%s","PR_MERGED":%s,"MERGE_COMMIT":"%s","DEFAULT_BRANCH":"%s"}\n' \
        "$SPEC_DIR" "$SPEC_FILE" "$SPEC_NAME" "$PR_URL" "$MERGE_DATE" "$BASELINE_FILE" "$PR_MERGED_JSON" "$MERGE_COMMIT" "$DEFAULT_BRANCH"
else
    echo "SPEC_DIR: $SPEC_DIR"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "SPEC_NAME: $SPEC_NAME"
    echo "PR_URL: ${PR_URL:-N/A}"
    echo "MERGE_DATE: ${MERGE_DATE:-N/A}"
    echo "BASELINE_FILE: ${BASELINE_FILE:-N/A}"
    echo "PR_MERGED: $PR_MERGED"
    echo "MERGE_COMMIT: ${MERGE_COMMIT:-N/A}"
    echo "DEFAULT_BRANCH: $DEFAULT_BRANCH"
fi
