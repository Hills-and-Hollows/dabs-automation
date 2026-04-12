#!/usr/bin/env bash
# spequa-common.sh — Shared helper functions for spequa-* scripts
# Source this file, do not execute directly.
# Compatible with bash 3.2+ (macOS default).

# Logging
spequa_info()  { echo "[spequa] $*"; }
spequa_warn()  { echo "[spequa] WARNING: $*" >&2; }
spequa_error() { echo "[spequa] ERROR: $*" >&2; }

# Compute relative path from $1 to $2
# Usage: spequa_relative_path /a/b/c /a/d/e → ../../d/e
spequa_relative_path() {
    local from="$1"
    local to="$2"

    # Normalize to absolute paths
    from="$(cd "$from" 2>/dev/null && pwd || echo "$from")"
    to="$(cd "$(dirname "$to")" 2>/dev/null && pwd)/$(basename "$to")" 2>/dev/null || to="$to"

    # Use python for reliable relative path computation
    python3 -c "import os; print(os.path.relpath('$to', '$from'))" 2>/dev/null || echo "$to"
}

# Agent folder name → agent key lookup (bash 3.2 compatible, no associative arrays)
spequa_folder_to_key() {
    case "$1" in
        .github)    echo "copilot" ;;
        .claude)    echo "claude" ;;
        .gemini)    echo "gemini" ;;
        .cursor)    echo "cursor-agent" ;;
        .qwen)      echo "qwen" ;;
        .opencode)  echo "opencode" ;;
        .codex)     echo "codex" ;;
        .windsurf)  echo "windsurf" ;;
        .kilocode)  echo "kilocode" ;;
        .augment)   echo "auggie" ;;
        .codebuddy) echo "codebuddy" ;;
        .qoder)     echo "qodercli" ;;
        .roo)       echo "roo" ;;
        .kiro)      echo "kiro-cli" ;;
        .agents)    echo "amp" ;;
        .shai)      echo "shai" ;;
        .agent)     echo "agy" ;;
        .bob)       echo "bob" ;;
        .comet)     echo "comet" ;;
        *)          echo "" ;;
    esac
}

# Agent key → folder name lookup
spequa_key_to_folder() {
    case "$1" in
        copilot)      echo ".github" ;;
        claude)       echo ".claude" ;;
        gemini)       echo ".gemini" ;;
        cursor-agent) echo ".cursor" ;;
        qwen)         echo ".qwen" ;;
        opencode)     echo ".opencode" ;;
        codex)        echo ".codex" ;;
        windsurf)     echo ".windsurf" ;;
        kilocode)     echo ".kilocode" ;;
        auggie)       echo ".augment" ;;
        codebuddy)    echo ".codebuddy" ;;
        qodercli)     echo ".qoder" ;;
        roo)          echo ".roo" ;;
        kiro-cli)     echo ".kiro" ;;
        amp)          echo ".agents" ;;
        shai)         echo ".shai" ;;
        agy)          echo ".agent" ;;
        bob)          echo ".bob" ;;
        comet)        echo ".comet" ;;
        *)            echo "" ;;
    esac
}

# All known agent keys (space-separated)
EQUASPEC_ALL_AGENT_KEYS="copilot claude gemini cursor-agent qwen opencode codex windsurf kilocode auggie codebuddy qodercli roo kiro-cli amp shai agy bob comet"

# .spequa.json read/write (pure shell, no jq dependency)
# Write: spequa_json_write FILE PINNED LAST_SYNC TOOLKIT_VERSION [AGENTS_JSON_ARRAY]
spequa_json_write() {
    local file="$1"
    local pinned="${2:-false}"
    local last_sync="${3:-}"
    local toolkit_version="${4:-}"
    local agents_json="${5:-}"

    # Quote strings, leave null unquoted; treat empty as null
    local sync_val="null"
    [[ -n "$last_sync" ]] && sync_val="\"$last_sync\""

    local ver_val="null"
    [[ -n "$toolkit_version" ]] && ver_val="\"$toolkit_version\""

    # Agents array: if provided use it, otherwise preserve existing or omit
    local agents_val=""
    if [[ -n "$agents_json" ]]; then
        agents_val="$agents_json"
    elif [[ -f "$file" ]]; then
        agents_val="$(spequa_json_read_agents "$file")"
    fi

    if [[ -n "$agents_val" && "$agents_val" != "null" ]]; then
        cat > "$file" <<EOF
{
  "pinned": $pinned,
  "agents": $agents_val,
  "last_sync": $sync_val,
  "toolkit_version": $ver_val
}
EOF
    else
        cat > "$file" <<EOF
{
  "pinned": $pinned,
  "last_sync": $sync_val,
  "toolkit_version": $ver_val
}
EOF
    fi
}

# Read pinned field from .spequa.json
spequa_json_read_pinned() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "false"
        return
    fi
    # Extract pinned value (true/false)
    grep -o '"pinned"[[:space:]]*:[[:space:]]*[a-z]*' "$file" | grep -o 'true\|false' || echo "false"
}

# Read toolkit_version from .spequa.json
spequa_json_read_version() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "unknown"
        return
    fi
    local val
    val="$(grep -o '"toolkit_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$file" | sed 's/.*: *"\([^"]*\)"/\1/' 2>/dev/null || echo "")"
    [[ -n "$val" ]] && echo "$val" || echo "unknown"
}

# Read last_sync from .spequa.json
spequa_json_read_last_sync() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi
    local val
    val="$(grep -o '"last_sync"[[:space:]]*:[[:space:]]*"[^"]*"' "$file" | sed 's/.*: *"\([^"]*\)"/\1/' 2>/dev/null || echo "")"
    echo "$val"
}

# Read agents array from .spequa.json as raw JSON
# Returns the JSON array string, e.g. ["claude", "cursor-agent", "agy"]
spequa_json_read_agents() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi
    python3 -c "
import json
try:
    with open('$file') as f:
        data = json.load(f)
    agents = data.get('agents')
    if agents and isinstance(agents, list):
        print(json.dumps(agents))
    else:
        print('')
except:
    print('')
" 2>/dev/null || echo ""
}

# Read agents as a space-separated list of agent keys
spequa_json_read_agents_list() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi
    python3 -c "
import json
try:
    with open('$file') as f:
        data = json.load(f)
    agents = data.get('agents')
    if agents and isinstance(agents, list):
        print(' '.join(agents))
    else:
        print('')
except:
    print('')
" 2>/dev/null || echo ""
}

# Check if an agent folder name is in the configured agents list
# Usage: spequa_agent_allowed ".claude" ".spequa.json"
# Returns 0 (true) if allowed, 1 (false) if not
spequa_agent_allowed() {
    local folder_name="$1"
    local config_file="$2"

    # If no agents field in config, allow all (backward compatibility)
    local agents_list
    agents_list="$(spequa_json_read_agents_list "$config_file")"
    if [[ -z "$agents_list" ]]; then
        return 0  # No filter = allow all
    fi

    # Look up the agent key for this folder
    local agent_key
    agent_key="$(spequa_folder_to_key "$folder_name")"
    if [[ -z "$agent_key" ]]; then
        return 1  # Unknown folder = skip
    fi

    # Check if agent_key is in the list
    for key in $agents_list; do
        if [[ "$key" == "$agent_key" ]]; then
            return 0
        fi
    done
    return 1
}
