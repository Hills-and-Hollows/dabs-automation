#!/usr/bin/env bash
# spequa-link.sh — Create/refresh symlinks from project dirs to submodule
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/spequa-common.sh"

DRY_RUN=false
VERBOSE=false
SUBMODULE_PATH=".spequa"
CONFIG_FILE=".spequa.json"

usage() {
    cat <<'EOF'
Usage: spequa-link.sh [OPTIONS]

Create or refresh symlinks from project directories to the .spequa/ submodule.
Idempotent — safe to run multiple times.

Options:
  --dry-run    Show what would be linked without making changes
  --verbose    Print each symlink created/skipped
  --help       Show this help message

Override detection:
  If a real file (not a symlink) exists at a target path, it is treated as a
  project-level override. The symlink is skipped for that file.

Exit codes:
  0 — Success
  1 — .spequa/ not found
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --help) usage; exit 0 ;;
        *) spequa_error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [[ ! -d "$SUBMODULE_PATH" ]]; then
    spequa_error ".spequa/ submodule not found. Run spequa-bootstrap.sh first."
    exit 1
fi

CREATED=0
SKIPPED=0
ORPHANED=0

# Create a relative symlink from $target to $source
# $1 = source (inside .spequa/)
# $2 = target (project path)
create_symlink() {
    local source="$1"
    local target="$2"

    # If target is a real file (not symlink), it's an override — skip
    if [[ -f "$target" ]] && [[ ! -L "$target" ]]; then
        SKIPPED=$((SKIPPED + 1))
        if [[ "$VERBOSE" == true ]]; then
            spequa_info "SKIP (override): $target"
        fi
        return
    fi

    # Remove stale symlink if it exists
    if [[ -L "$target" ]]; then
        if [[ "$DRY_RUN" != true ]]; then
            rm "$target"
        fi
    fi

    # Compute relative path from target's directory to source
    local target_dir
    target_dir="$(dirname "$target")"
    local rel_path
    rel_path="$(spequa_relative_path "$target_dir" "$source")"

    if [[ "$DRY_RUN" == true ]]; then
        spequa_info "WOULD LINK: $target -> $rel_path"
    else
        mkdir -p "$target_dir"
        ln -s "$rel_path" "$target"
        if [[ "$VERBOSE" == true ]]; then
            spequa_info "LINK: $target -> $rel_path"
        fi
    fi
    CREATED=$((CREATED + 1))
}

# Create a directory symlink
# $1 = source dir (inside .spequa/)
# $2 = target dir (project path)
create_dir_symlink() {
    local source="$1"
    local target="$2"

    # If target is a real directory (not symlink), it's an override — skip
    if [[ -d "$target" ]] && [[ ! -L "$target" ]]; then
        SKIPPED=$((SKIPPED + 1))
        if [[ "$VERBOSE" == true ]]; then
            spequa_info "SKIP (override dir): $target"
        fi
        return
    fi

    # Remove stale symlink
    if [[ -L "$target" ]]; then
        if [[ "$DRY_RUN" != true ]]; then
            rm "$target"
        fi
    fi

    local target_parent
    target_parent="$(dirname "$target")"
    local rel_path
    rel_path="$(spequa_relative_path "$target_parent" "$source")"

    if [[ "$DRY_RUN" == true ]]; then
        spequa_info "WOULD LINK DIR: $target -> $rel_path"
    else
        mkdir -p "$target_parent"
        ln -s "$rel_path" "$target"
        if [[ "$VERBOSE" == true ]]; then
            spequa_info "LINK DIR: $target -> $rel_path"
        fi
    fi
    CREATED=$((CREATED + 1))
}

# 1. Dynamically discover and symlink agent command directories
# Matches any subdirectory inside dot-prefixed agent dirs:
#   .claude/commands/, .cursor/commands/, .gemini/commands/  (standard)
#   .github/agents/   (Copilot)
#   .agent/workflows/  (Antigravity)
#   .windsurf/workflows/, .codex/prompts/, .kiro/prompts/   (others)
for agent_dir in "$SUBMODULE_PATH"/.*; do
    [[ -d "$agent_dir" ]] || continue
    agent_name="$(basename "$agent_dir")"

    # Skip . and .. and .git
    [[ "$agent_name" == "." || "$agent_name" == ".." || "$agent_name" == ".git" ]] && continue

    # Skip .spequa (handled separately below)
    [[ "$agent_name" == ".spequa" ]] && continue

    # Filter by agents list in .spequa.json (if configured)
    if ! spequa_agent_allowed "$agent_name" "$CONFIG_FILE"; then
        if [[ "$VERBOSE" == true ]]; then
            spequa_info "SKIP (not in agents list): $agent_name"
        fi
        continue
    fi

    # Discover subdirectories that contain spequa command files (spequa.*.md)
    # This safely skips non-agent dirs like .github/workflows/ and .github/ISSUE_TEMPLATE/
    for cmd_dir in "$agent_dir"/*/; do
        [[ -d "$cmd_dir" ]] || continue

        # Only process directories that contain spequa.* files
        has_cmdfile=false
        for check in "$cmd_dir"/spequa.*; do
            [[ -f "$check" ]] && has_cmdfile=true && break
        done
        [[ "$has_cmdfile" == true ]] || continue

        # Symlink each file individually (enables per-file overrides)
        for file in "$cmd_dir"/*; do
            [[ -f "$file" ]] || continue
            local_file="${file#$SUBMODULE_PATH/}"
            create_symlink "$file" "$local_file"
        done
    done
done

# 2. Symlink .spequa/scripts/ and .spequa/templates/ (directory-level)
if [[ -d "$SUBMODULE_PATH/.spequa/scripts" ]]; then
    create_dir_symlink "$SUBMODULE_PATH/.spequa/scripts" ".spequa/scripts"
fi

if [[ -d "$SUBMODULE_PATH/.spequa/templates" ]]; then
    create_dir_symlink "$SUBMODULE_PATH/.spequa/templates" ".spequa/templates"
fi

# 3. NEVER symlink project-local files — they must remain under project control:
#    - .spequa/memory/     (project constitution and memory)
#    - .spequa/config.yml  (project configuration — spec 006)
#    - .spequa/overrides/  (per-section command overrides — spec 006)

# 4. Detect orphaned overrides (real files with no submodule equivalent)
for agent_dir in .*; do
    [[ -d "$agent_dir" ]] || continue
    agent_name="$(basename "$agent_dir")"
    [[ "$agent_name" == "." || "$agent_name" == ".." || "$agent_name" == ".git" || "$agent_name" == ".spequa" ]] && continue
    [[ "$agent_name" == ".spequa" ]] && continue
    # Only check subdirectories that contain spequa command files
    for cmd_dir in "$agent_dir"/*/; do
        [[ -d "$cmd_dir" ]] || continue
        # Skip dirs without spequa.* files (e.g. .github/workflows/)
        has_cmdfile=false
        for check in "$cmd_dir"/spequa.*; do
            [[ -e "$check" ]] && has_cmdfile=true && break
        done
        [[ "$has_cmdfile" == true ]] || continue
        for file in "$cmd_dir"/*; do
            [[ -f "$file" ]] && [[ ! -L "$file" ]] || continue
            # This is a real file (potential override). Check if submodule has equivalent.
            submodule_equiv="$SUBMODULE_PATH/$file"
            if [[ ! -f "$submodule_equiv" ]]; then
                ORPHANED=$((ORPHANED + 1))
                spequa_warn "Orphaned override: $file (no upstream equivalent in $submodule_equiv)"
            fi
        done
    done
done

# Report
spequa_info "Symlink summary: $CREATED created, $SKIPPED overrides skipped, $ORPHANED orphaned"
