#!/usr/bin/env bash
# sync-templates.sh — Propagate templates/commands/ to all agent directories
#
# Reads numbered master templates (e.g. 5-plan.md) and generates numbered
# agent commands (spequa.5-plan.md) in markdown or TOML format per agent.
# Also cleans up any legacy unnumbered aliases (spequa.plan.md).
# Compatible with bash 3.2+ (macOS default).
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"

source "$SCRIPT_DIR/spequa-common.sh"

DRY_RUN=false
VERBOSE=false
FORCE=false

usage() {
    cat <<'EOF'
Usage: sync-templates.sh [OPTIONS]

Propagate templates/commands/ to all agent directories.

Each master template (e.g. 5-plan.md) produces one file per agent:
  - spequa.5-plan.{md,toml}   (numbered, pipeline-aware)

Legacy unnumbered aliases (spequa.plan.md) are cleaned up automatically.

Options:
  --dry-run    Show what would be written without making changes
  --verbose    Print each file written/skipped
  --force      Overwrite even if target is newer than template
  --help       Show this help message

Exit codes:
  0 — Success
  1 — templates/commands/ not found
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --force)   FORCE=true; shift ;;
        --help)    usage; exit 0 ;;
        *)         spequa_error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

TEMPLATES_DIR="$REPO_ROOT/templates/commands"
if [[ ! -d "$TEMPLATES_DIR" ]]; then
    spequa_error "templates/commands/ not found at $REPO_ROOT"
    exit 1
fi

# ─── Agent directory map ──────────────────────────────────────────────
# Format: "folder:subdir:format:arg_placeholder"
# format = md | toml
# arg_placeholder = what replaces $ARGUMENTS in the template
AGENT_MAP=(
    ".claude:commands:md:\$ARGUMENTS"
    ".cursor:commands:md:\$ARGUMENTS"
    ".augment:commands:md:\$ARGUMENTS"
    ".bob:commands:md:\$ARGUMENTS"
    ".comet:commands:md:\$ARGUMENTS"
    ".codebuddy:commands:md:\$ARGUMENTS"
    ".qoder:commands:md:\$ARGUMENTS"
    ".roo:commands:md:\$ARGUMENTS"
    ".shai:commands:md:\$ARGUMENTS"
    ".agents:commands:md:\$ARGUMENTS"
    ".agent:workflows:md:\$ARGUMENTS"
    ".codex:prompts:md:\$ARGUMENTS"
    ".kiro:prompts:md:\$ARGUMENTS"
    ".opencode:command:md:\$ARGUMENTS"
    ".windsurf:workflows:md:\$ARGUMENTS"
    ".kilocode:workflows:md:\$ARGUMENTS"
    ".github:agents:md:\$ARGUMENTS"
    ".gemini:commands:toml:{{args}}"
    ".qwen:commands:toml:{{args}}"
)

WRITTEN=0
SKIPPED=0
ERRORS=0
CLEANED=0

# ─── Helper: extract YAML frontmatter description ────────────────────
extract_description() {
    local file="$1"
    python3 - "$file" <<'PYEOF'
import re, sys
content = open(sys.argv[1]).read()
m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if m:
    fm = m.group(1)
    # Try quoted first, then unquoted
    dm = re.search(r'description:\s*["\'](.+?)["\']', fm)
    if not dm:
        dm = re.search(r'description:\s*(.+)', fm)
    if dm:
        print(dm.group(1).strip().strip('"').strip("'"))
PYEOF
}

# ─── Helper: extract body (everything after YAML frontmatter) ────────
extract_body() {
    local file="$1"
    python3 - "$file" <<'PYEOF'
import re, sys
content = open(sys.argv[1]).read()
m = re.match(r'^---\n.*?\n---\n?', content, re.DOTALL)
if m:
    print(content[m.end():], end='')
else:
    print(content, end='')
PYEOF
}

# ─── Helper: strip number prefixes from cross-references ─────────────
# /spequa.5-plan → /spequa.plan
# /spequa.14.1-pr-checks → /spequa.pr-checks
# spequa.3-spequafy → spequa.spequafy (non-slash contexts too)
strip_number_refs() {
    # Use sed to strip number prefixes from spequa references
    sed -E 's|(/spequa\.)([0-9]+(\.[0-9]+)?)-|\1|g; s|(spequa\.)([0-9]+(\.[0-9]+)?)-|\1|g'
}

# ─── Helper: render TOML wrapper ─────────────────────────────────────
render_toml() {
    local description="$1"
    local body="$2"
    local escaped_desc
    escaped_desc="$(echo "$description" | sed 's/"/\\"/g')"
    printf 'description = "%s"\n\nprompt = """\n%s\n"""\n' "$escaped_desc" "$body"
}

# ─── Helper: write one agent file ────────────────────────────────────
# $1 = dest_path, $2 = content
write_file() {
    local dest="$1"
    local content="$2"

    if [[ "$DRY_RUN" == true ]]; then
        [[ "$VERBOSE" == true ]] && spequa_info "WOULD WRITE: $dest"
        WRITTEN=$((WRITTEN + 1))
        return
    fi

    mkdir -p "$(dirname "$dest")"
    printf '%s' "$content" > "$dest"
    [[ "$VERBOSE" == true ]] && spequa_info "WRITE: $dest"
    WRITTEN=$((WRITTEN + 1))
}

# ─── Main loop ────────────────────────────────────────────────────────
for template in "$TEMPLATES_DIR"/*.md; do
    [[ -f "$template" ]] || continue

    tpl_basename="$(basename "$template")"

    # Parse numbered filename: "5-plan.md" → order="5", stem="plan"
    if [[ "$tpl_basename" =~ ^([0-9]+(\.[0-9]+)?)-(.+)\.md$ ]]; then
        order="${BASH_REMATCH[1]}"
        stem="${BASH_REMATCH[3]}"
    else
        spequa_warn "Skipping non-numbered template: $tpl_basename"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    description="$(extract_description "$template")"
    body="$(extract_body "$template")"

    if [[ -z "$body" ]]; then
        spequa_warn "Empty body in $tpl_basename — skipping"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # For each agent, generate numbered + unnumbered variants
    for entry in "${AGENT_MAP[@]}"; do
        IFS=':' read -r folder subdir format arg_placeholder <<< "$entry"

        agent_dir="$REPO_ROOT/$folder/$subdir"

        # Skip agents whose directory doesn't exist in this repo
        [[ -d "$agent_dir" ]] || continue

        # ── Prepare body with correct arg placeholder ──
        agent_body="$body"
        if [[ "$arg_placeholder" != '$ARGUMENTS' ]]; then
            agent_body="$(echo "$agent_body" | sed "s/\\\$ARGUMENTS/$arg_placeholder/g")"
        fi

        # ── Numbered variant ──
        if [[ "$format" == "toml" ]]; then
            numbered_name="spequa.${order}-${stem}.toml"
            numbered_content="$(render_toml "$description" "$agent_body")"
        else
            numbered_name="spequa.${order}-${stem}.md"
            # Markdown: description-only frontmatter
            numbered_content="$(printf -- '---\ndescription: %s\n---\n%s' "$description" "$agent_body")"
        fi
        write_file "$agent_dir/$numbered_name" "$numbered_content"

        # ── Clean up legacy unnumbered aliases if present ──
        if [[ "$format" == "toml" ]]; then
            legacy="$agent_dir/spequa.${stem}.toml"
        else
            legacy="$agent_dir/spequa.${stem}.md"
        fi
        if [[ -f "$legacy" ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                [[ "$VERBOSE" == true ]] && spequa_info "WOULD DELETE: $legacy"
            else
                rm "$legacy"
                [[ "$VERBOSE" == true ]] && spequa_info "DELETE: $legacy (unnumbered alias)"
            fi
            CLEANED=$((CLEANED + 1))
        fi
    done
done

# ─── Report ───────────────────────────────────────────────────────────
mode="sync"
[[ "$DRY_RUN" == true ]] && mode="dry-run"
spequa_info "Template $mode complete: $WRITTEN written, $CLEANED cleaned, $SKIPPED skipped, $ERRORS errors"
