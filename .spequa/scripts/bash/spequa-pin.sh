#!/usr/bin/env bash
# spequa-pin.sh — Pin/unpin toolkit version
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/spequa-common.sh"

SUBMODULE_PATH=".spequa"
CONFIG_FILE=".spequa.json"

usage() {
    cat <<'EOF'
Usage: spequa-pin.sh COMMAND [OPTIONS]

Manage toolkit version pinning.

Commands:
  pin [--version SHA]   Pin to current or specified commit
  unpin                 Unpin and trigger sync
  status                Show current pin state and version

Options:
  --version SHA   Pin to a specific commit SHA (with 'pin' command)
  --help          Show this help message

Exit codes:
  0 — Success
  1 — .spequa.json not found
  2 — Invalid SHA (for --version)
EOF
}

if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

COMMAND="$1"
shift

# Handle --help as a command (before precondition checks)
if [[ "$COMMAND" == "--help" || "$COMMAND" == "-h" ]]; then
    usage
    exit 0
fi

VERSION_SHA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version) VERSION_SHA="$2"; shift 2 ;;
        --help) usage; exit 0 ;;
        *) spequa_error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [[ ! -f "$CONFIG_FILE" ]]; then
    spequa_error ".spequa.json not found. Run spequa-bootstrap.sh first."
    exit 1
fi

case "$COMMAND" in
    pin)
        if [[ -n "$VERSION_SHA" ]]; then
            # Validate and checkout specific commit
            if ! git -C "$SUBMODULE_PATH" cat-file -t "$VERSION_SHA" >/dev/null 2>&1; then
                spequa_error "Invalid SHA: $VERSION_SHA"
                exit 2
            fi
            spequa_info "Checking out $VERSION_SHA in submodule..."
            git -C "$SUBMODULE_PATH" checkout "$VERSION_SHA" 2>/dev/null
        fi

        local_version="$(git -C "$SUBMODULE_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
        local_timestamp="$(spequa_json_read_last_sync "$CONFIG_FILE")"
        spequa_json_write "$CONFIG_FILE" "true" "$local_timestamp" "$local_version"
        spequa_info "Pinned to $local_version. Auto-sync disabled."
        ;;

    unpin)
        local_version="$(git -C "$SUBMODULE_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
        local_timestamp="$(spequa_json_read_last_sync "$CONFIG_FILE")"
        spequa_json_write "$CONFIG_FILE" "false" "$local_timestamp" "$local_version"
        spequa_info "Unpinned. Auto-sync re-enabled."

        # Trigger sync
        spequa_info "Syncing..."
        "$SCRIPT_DIR/spequa-sync.sh"
        ;;

    status)
        pinned="$(spequa_json_read_pinned "$CONFIG_FILE")"
        version="$(spequa_json_read_version "$CONFIG_FILE")"
        last_sync="$(spequa_json_read_last_sync "$CONFIG_FILE")"
        current_ref="$(git -C "$SUBMODULE_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown")"

        echo "Toolkit Status:"
        echo "  Pinned:     $pinned"
        echo "  Version:    $version"
        echo "  Current:    $current_ref"
        echo "  Last sync:  ${last_sync:-never}"
        ;;

    *)
        spequa_error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
