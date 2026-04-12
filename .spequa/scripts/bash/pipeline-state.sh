#!/usr/bin/env bash

# CRUD operations for .pipeline-state.json in a spec feature directory.
#
# Usage: ./pipeline-state.sh <subcommand> [options]
#
# Subcommands:
#   init     Create a new .pipeline-state.json
#   read     Output current pipeline state
#   update   Update phase, status, or artifact entries
#   lock     Acquire PID-based lock
#   unlock   Release lock
#
# Exit code: 0 on success, 1 on error

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

STATE_FILE=".pipeline-state.json"

# --- Helpers ---

iso8601_now() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

unix_timestamp() {
    date +%s
}

# Resolve feature directory: explicit override or auto-detect
resolve_feature_dir() {
    local override="$1"
    if [[ -n "$override" ]]; then
        if [[ ! "$override" = /* ]]; then
            override="$(cd "$override" && pwd)"
        fi
        echo "$override"
        return
    fi

    local repo_root
    repo_root=$(get_repo_root)
    local branch
    branch=$(get_current_branch)
    find_feature_dir_by_prefix "$repo_root" "$branch"
}

state_path() {
    echo "$1/$STATE_FILE"
}

err() {
    echo "{\"error\":\"$1\"}" >&2
    exit 1
}

# JSON string escaping
json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    echo "$s"
}

# Update a top-level string field using jq or sed fallback
json_set_string() {
    local file="$1" key="$2" value="$3"
    if command -v jq >/dev/null 2>&1; then
        local tmp
        tmp=$(jq --arg v "$value" ".$key = \$v" "$file")
        echo "$tmp" > "$file"
    else
        sed -i.bak "s|\"$key\":[[:space:]]*\"[^\"]*\"|\"$key\": \"$value\"|" "$file"
        rm -f "${file}.bak"
    fi
}

# Update a top-level null-able field to null
json_set_null() {
    local file="$1" key="$2"
    if command -v jq >/dev/null 2>&1; then
        local tmp
        tmp=$(jq ".$key = null" "$file")
        echo "$tmp" > "$file"
    else
        sed -i.bak "s|\"$key\":[[:space:]]*\"[^\"]*\"|\"$key\": null|; s|\"$key\":[[:space:]]*[0-9]*|\"$key\": null|" "$file"
        rm -f "${file}.bak"
    fi
}

# --- Subcommands ---

cmd_init() {
    local feature_dir="$1"
    shift
    local spec_id="" feature_name="" autonomy_level="HIGH" timeout="60"
    local deploy_target="none" score_threshold="10"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --spec-id) spec_id="$2"; shift 2 ;;
            --feature-name) feature_name="$2"; shift 2 ;;
            --autonomy-level) autonomy_level="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            --deploy-target) deploy_target="$2"; shift 2 ;;
            --score-threshold) score_threshold="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    # Auto-detect spec_id from directory name if not provided
    if [[ -z "$spec_id" ]]; then
        local dirname
        dirname=$(basename "$feature_dir")
        if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
            spec_id="${BASH_REMATCH[1]}"
        fi
    fi

    # Auto-detect feature_name from directory name if not provided
    if [[ -z "$feature_name" ]]; then
        feature_name=$(basename "$feature_dir")
    fi

    local ts
    ts=$(unix_timestamp)
    local run_id="${spec_id}-${ts}"
    local now
    now=$(iso8601_now)
    local filepath
    filepath=$(state_path "$feature_dir")

    cat > "$filepath" <<ENDJSON
{"schema_version":"1.0","run_id":"${run_id}","spec_id":"$(json_escape "$spec_id")","feature_name":"$(json_escape "$feature_name")","status":"running","started_at":"${now}","completed_at":null,"config":{"autonomy_level":"${autonomy_level}","max_retries_per_phase":3,"timeout_minutes":${timeout},"target_repo":"","branch_from":"main","deploy_target":"${deploy_target}","score_threshold":${score_threshold},"pause_on_destructive":true},"phases":[],"decisions":[],"retries":[],"pause":{"active":false,"phase":null,"reason":null,"question":null,"options":[],"paused_at":null},"lock":{"pid":null,"acquired_at":null},"score":{"total_applicable":0,"total_passed":0,"verdict":null,"requirements":[]}}
ENDJSON

    cat "$filepath"
}

cmd_read() {
    local feature_dir="$1"
    local filepath
    filepath=$(state_path "$feature_dir")

    if [[ ! -f "$filepath" ]]; then
        err "Pipeline state file not found: $filepath"
    fi

    cat "$filepath"
}

cmd_update() {
    local feature_dir="$1"
    shift
    local filepath
    filepath=$(state_path "$feature_dir")

    if [[ ! -f "$filepath" ]]; then
        err "Pipeline state file not found: $filepath"
    fi

    local phase="" phase_status="" gate_result="" status="" add_artifact=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --phase) phase="$2"; shift 2 ;;
            --phase-status) phase_status="$2"; shift 2 ;;
            --gate-result) gate_result="$2"; shift 2 ;;
            --status) status="$2"; shift 2 ;;
            --add-artifact) add_artifact="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    # Update pipeline-level status
    if [[ -n "$status" ]]; then
        json_set_string "$filepath" "status" "$status"
        if [[ "$status" == "completed" || "$status" == "failed" ]]; then
            json_set_string "$filepath" "completed_at" "$(iso8601_now)"
        fi
    fi

    # Update phase entry
    if [[ -n "$phase" ]] && command -v jq >/dev/null 2>&1; then
        local phase_idx="$phase"

        # Ensure phases array is large enough
        local phases_len
        phases_len=$(jq '.phases | length' "$filepath")

        while [[ "$phases_len" -le "$phase_idx" ]]; do
            local tmp
            tmp=$(jq '.phases += [{"phase": '"$phases_len"', "status": "pending", "gate_result": null, "artifacts": [], "started_at": null, "completed_at": null}]' "$filepath")
            echo "$tmp" > "$filepath"
            phases_len=$((phases_len + 1))
        done

        if [[ -n "$phase_status" ]]; then
            local tmp
            tmp=$(jq --arg s "$phase_status" ".phases[$phase_idx].status = \$s" "$filepath")
            echo "$tmp" > "$filepath"
            if [[ "$phase_status" == "running" ]]; then
                tmp=$(jq --arg t "$(iso8601_now)" ".phases[$phase_idx].started_at = \$t" "$filepath")
                echo "$tmp" > "$filepath"
            elif [[ "$phase_status" == "completed" || "$phase_status" == "failed" ]]; then
                tmp=$(jq --arg t "$(iso8601_now)" ".phases[$phase_idx].completed_at = \$t" "$filepath")
                echo "$tmp" > "$filepath"
            fi
        fi

        if [[ -n "$gate_result" ]]; then
            local tmp
            tmp=$(jq --arg g "$gate_result" ".phases[$phase_idx].gate_result = \$g" "$filepath")
            echo "$tmp" > "$filepath"
        fi

        if [[ -n "$add_artifact" ]]; then
            local tmp
            tmp=$(jq --arg a "$add_artifact" ".phases[$phase_idx].artifacts += [\$a]" "$filepath")
            echo "$tmp" > "$filepath"
        fi
    elif [[ -n "$phase" ]] && [[ -z "$(command -v jq)" ]]; then
        echo "{\"warning\":\"Phase updates require jq; install jq for phase-level operations\"}" >&2
    fi

    cat "$filepath"
}

cmd_lock() {
    local feature_dir="$1"
    local filepath
    filepath=$(state_path "$feature_dir")

    if [[ ! -f "$filepath" ]]; then
        err "Pipeline state file not found: $filepath"
    fi

    # Check existing lock
    if command -v jq >/dev/null 2>&1; then
        local existing_pid
        existing_pid=$(jq -r '.lock.pid // empty' "$filepath")

        if [[ -n "$existing_pid" ]] && [[ "$existing_pid" != "null" ]]; then
            # Check if PID is still alive
            if kill -0 "$existing_pid" 2>/dev/null; then
                err "Lock held by active process $existing_pid"
            fi
            # PID is dead, reclaim
        fi

        local tmp
        tmp=$(jq --argjson pid $$ --arg t "$(iso8601_now)" '.lock.pid = $pid | .lock.acquired_at = $t' "$filepath")
        echo "$tmp" > "$filepath"
    else
        # Fallback: simple sed-based lock
        local existing_pid
        existing_pid=$(grep -o '"pid":[[:space:]]*[0-9]*' "$filepath" | grep -o '[0-9]*' || true)

        if [[ -n "$existing_pid" ]]; then
            if kill -0 "$existing_pid" 2>/dev/null; then
                err "Lock held by active process $existing_pid"
            fi
        fi

        sed -i.bak "s|\"pid\":[[:space:]]*[^,}]*|\"pid\": $$|; s|\"acquired_at\":[[:space:]]*[^,}]*|\"acquired_at\": \"$(iso8601_now)\"|" "$filepath"
        rm -f "${filepath}.bak"
    fi

    cat "$filepath"
}

cmd_unlock() {
    local feature_dir="$1"
    local filepath
    filepath=$(state_path "$feature_dir")

    if [[ ! -f "$filepath" ]]; then
        err "Pipeline state file not found: $filepath"
    fi

    if command -v jq >/dev/null 2>&1; then
        local tmp
        tmp=$(jq '.lock.pid = null | .lock.acquired_at = null' "$filepath")
        echo "$tmp" > "$filepath"
    else
        sed -i.bak 's|"pid":[[:space:]]*[^,}]*|"pid": null|; s|"acquired_at":[[:space:]]*[^,}]*|"acquired_at": null|' "$filepath"
        rm -f "${filepath}.bak"
    fi

    cat "$filepath"
}

# --- Main ---

SUBCOMMAND=""
FEATURE_DIR_OVERRIDE=""
JSON_FLAG=false
EXTRA_ARGS=()

# Parse global flags and subcommand
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_FLAG=true; shift ;;
        --feature-dir) FEATURE_DIR_OVERRIDE="$2"; shift 2 ;;
        init|read|update|lock|unlock)
            if [[ -z "$SUBCOMMAND" ]]; then
                SUBCOMMAND="$1"
                shift
            else
                EXTRA_ARGS+=("$1")
                shift
            fi
            ;;
        *) EXTRA_ARGS+=("$1"); shift ;;
    esac
done

if [[ -z "$SUBCOMMAND" ]]; then
    err "Usage: pipeline-state.sh <init|read|update|lock|unlock> [options]"
fi

FEATURE_DIR=$(resolve_feature_dir "$FEATURE_DIR_OVERRIDE")

if [[ ! -d "$FEATURE_DIR" ]] && [[ "$SUBCOMMAND" != "init" ]]; then
    err "Feature directory not found: $FEATURE_DIR"
fi

# Ensure directory exists for init
if [[ "$SUBCOMMAND" == "init" ]] && [[ ! -d "$FEATURE_DIR" ]]; then
    mkdir -p "$FEATURE_DIR"
fi

case "$SUBCOMMAND" in
    init)   cmd_init "$FEATURE_DIR" "${EXTRA_ARGS[@]}" ;;
    read)   cmd_read "$FEATURE_DIR" ;;
    update) cmd_update "$FEATURE_DIR" "${EXTRA_ARGS[@]}" ;;
    lock)   cmd_lock "$FEATURE_DIR" ;;
    unlock) cmd_unlock "$FEATURE_DIR" ;;
    *)      err "Unknown subcommand: $SUBCOMMAND" ;;
esac

exit 0
