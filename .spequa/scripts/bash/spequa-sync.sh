#!/usr/bin/env bash
# spequa-sync.sh — Pre-command hook: check and pull submodule updates
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/spequa-common.sh"

FORCE=false
QUIET=false
SUBMODULE_PATH=".spequa"
CONFIG_FILE=".spequa.json"

usage() {
    cat <<'EOF'
Usage: spequa-sync.sh [OPTIONS]

Pre-command hook: checks for toolkit updates and pulls if available.
Skips update if version is pinned (unless --force).

Options:
  --force    Sync even if pinned
  --quiet    Suppress informational output
  --help     Show this help message

Exit codes:
  0 — Success (including skipped-due-to-pin and offline-fallback)
  1 — .spequa/ not found
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force) FORCE=true; shift ;;
        --quiet) QUIET=true; shift ;;
        --help) usage; exit 0 ;;
        *) spequa_error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [[ ! -d "$SUBMODULE_PATH" ]]; then
    spequa_error ".spequa/ submodule not found. Run spequa-bootstrap.sh first."
    exit 1
fi

# Check pin state
pinned="$(spequa_json_read_pinned "$CONFIG_FILE")"
if [[ "$pinned" == "true" ]] && [[ "$FORCE" != true ]]; then
    if [[ "$QUIET" != true ]]; then
        spequa_info "Toolkit is pinned. Skipping sync. Use --force to override."
    fi
    exit 0
fi

# Attempt submodule update
if [[ "$QUIET" != true ]]; then
    spequa_info "Checking for toolkit updates..."
fi

if git submodule update --remote --merge "$SUBMODULE_PATH" 2>/dev/null; then
    # Success — refresh symlinks
    if [[ "$QUIET" == true ]]; then
        "$SCRIPT_DIR/spequa-link.sh" 2>/dev/null
    else
        "$SCRIPT_DIR/spequa-link.sh"
    fi

    # Update config
    local_version="$(git -C "$SUBMODULE_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
    local_timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    spequa_json_write "$CONFIG_FILE" "$pinned" "$local_timestamp" "$local_version"

    if [[ "$QUIET" != true ]]; then
        spequa_info "Synced to $local_version."
    fi
else
    # Offline or unreachable — use cached version
    spequa_warn "Could not reach upstream. Using cached toolkit version."
    # Still refresh symlinks from current submodule state
    "$SCRIPT_DIR/spequa-link.sh" 2>/dev/null || true
fi

exit 0
