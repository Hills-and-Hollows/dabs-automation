#!/usr/bin/env bash

# Structural closure checks for /spequa.16-close
#
# Runs 5 deterministic checks against a spec directory and outputs
# structured JSON for the closure workflow to interpret.
#
# Usage: ./run-closure-checks.sh <FEATURE_DIR>
#
# Checks:
#   1. Required artifacts exist (spec.md, plan.md, tasks.md)
#   2. All tasks marked [x] (complete)
#   3. Spec status field value (reported, not enforced)
#   4. No [NEEDS CLARIFICATION] markers in any .md file
#   5. SC-* items extracted from spec.md
#
# Exit code: Always 0 (caller interprets JSON results)

set -e

FEATURE_DIR="${1:?Usage: run-closure-checks.sh <FEATURE_DIR>}"

# Normalize to absolute path
if [[ ! "$FEATURE_DIR" = /* ]]; then
    FEATURE_DIR="$(cd "$FEATURE_DIR" && pwd)"
fi

# --- Check 1: Required artifacts exist ---
missing_files=()
for required in spec.md plan.md tasks.md; do
    if [[ ! -f "$FEATURE_DIR/$required" ]]; then
        missing_files+=("$required")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    # BLOCKED — cannot proceed without required files
    missing_json=$(printf '"%s",' "${missing_files[@]}")
    missing_json="[${missing_json%,}]"
    cat <<EOF
{"overall":"BLOCKED","checks":[{"name":"required_artifacts","result":"BLOCK","detail":"Missing: ${missing_files[*]}"}],"missing_files":${missing_json},"tasks":{"total":0,"completed":0,"incomplete":0},"status_field":"","markers":[],"sc_items":[],"fr_items":[]}
EOF
    exit 0
fi

# --- Check 2: Task completion ---
total_tasks=0
completed_tasks=0
incomplete_tasks=0
incomplete_list=()

while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]\[[xX]\] ]]; then
        total_tasks=$((total_tasks + 1))
        completed_tasks=$((completed_tasks + 1))
    elif [[ "$line" =~ ^[[:space:]]*-[[:space:]]\[[[:space:]]\] ]]; then
        total_tasks=$((total_tasks + 1))
        incomplete_tasks=$((incomplete_tasks + 1))
        # Extract task ID and brief description
        task_text="${line#*\] }"
        task_text="${task_text:0:80}"
        incomplete_list+=("$task_text")
    fi
done < "$FEATURE_DIR/tasks.md"

if [[ $incomplete_tasks -gt 0 ]]; then
    task_result="FAIL"
    task_detail="$incomplete_tasks of $total_tasks tasks incomplete"
else
    task_result="PASS"
    task_detail="All $total_tasks tasks complete"
fi

# --- Check 3: Spec status field ---
status_field=""
while IFS= read -r line; do
    if [[ "$line" =~ ^\*\*Status\*\*:[[:space:]]*(.+) ]]; then
        status_field="${BASH_REMATCH[1]}"
        # Trim whitespace
        status_field="${status_field## }"
        status_field="${status_field%% }"
        break
    fi
done < "$FEATURE_DIR/spec.md"

# Report only — the close workflow handles status updates
status_result="PASS"
status_detail="Current status: ${status_field:-unknown}"

# --- Check 4: [NEEDS CLARIFICATION] markers ---
markers=()
while IFS= read -r mdfile; do
    line_num=0
    while IFS= read -r line; do
        line_num=$((line_num + 1))
        # Skip lines inside backtick code blocks
        if [[ "$line" =~ ^\`\`\` ]]; then
            # Toggle code block state
            if [[ "${in_code_block:-false}" == "false" ]]; then
                in_code_block=true
            else
                in_code_block=false
            fi
            continue
        fi
        if [[ "${in_code_block:-false}" == "true" ]]; then
            continue
        fi
        # Strip inline backtick-quoted references before checking
        stripped=$(echo "$line" | sed 's/`[^`]*`//g')
        # Also skip lines that are checklist items ABOUT the marker (e.g., "No [NEEDS CLARIFICATION] markers remain")
        if [[ "$stripped" == *"[NEEDS CLARIFICATION]"* ]] && \
           ! [[ "$stripped" =~ No[[:space:]]+\[NEEDS[[:space:]]CLARIFICATION\] ]] && \
           ! [[ "$stripped" =~ markers[[:space:]]remain ]]; then
            relpath="${mdfile#"$FEATURE_DIR/"}"
            markers+=("${relpath}:L${line_num}")
        fi
    done < "$mdfile"
    in_code_block=false
done < <(find "$FEATURE_DIR" -name '*.md' -type f 2>/dev/null)

if [[ ${#markers[@]} -gt 0 ]]; then
    marker_result="FAIL"
    marker_detail="${#markers[@]} unresolved marker(s) found"
else
    marker_result="PASS"
    marker_detail="No unresolved markers"
fi

# --- Check 5: Extract SC-* items from spec.md ---
sc_items=()
while IFS= read -r line; do
    if [[ "$line" =~ \*\*SC-([0-9]+)\*\*:[[:space:]]*(.+) ]]; then
        sc_id="SC-${BASH_REMATCH[1]}"
        sc_text="${BASH_REMATCH[2]}"
        sc_items+=("${sc_id}: ${sc_text}")
    fi
done < "$FEATURE_DIR/spec.md"

if [[ ${#sc_items[@]} -eq 0 ]]; then
    sc_result="FAIL"
    sc_detail="No success criteria (SC-*) found in spec.md; spec is malformed"
else
    sc_result="PASS"
    sc_detail="${#sc_items[@]} success criteria found"
fi

# --- Extract FR-* items from spec.md ---
fr_items=()
while IFS= read -r line; do
    if [[ "$line" =~ \*\*FR-([0-9]+)\*\*:[[:space:]]*(.+) ]]; then
        fr_id="FR-${BASH_REMATCH[1]}"
        fr_text="${BASH_REMATCH[2]}"
        fr_items+=("${fr_id}: ${fr_text}")
    fi
done < "$FEATURE_DIR/spec.md"

# --- Compute overall result ---
overall="PASS"
if [[ "$task_result" == "FAIL" || "$marker_result" == "FAIL" || "$sc_result" == "FAIL" ]]; then
    overall="FAIL"
fi

# --- Build JSON output ---
# Helper: array to JSON array of strings
to_json_array() {
    local arr=("$@")
    if [[ ${#arr[@]} -eq 0 ]]; then
        echo "[]"
        return
    fi
    local json="["
    local first=true
    for item in "${arr[@]}"; do
        # Escape double quotes and backslashes in the item
        item="${item//\\/\\\\}"
        item="${item//\"/\\\"}"
        if $first; then
            json+="\"${item}\""
            first=false
        else
            json+=",\"${item}\""
        fi
    done
    json+="]"
    echo "$json"
}

checks_json="["
checks_json+="{\"name\":\"required_artifacts\",\"result\":\"PASS\",\"detail\":\"All required files present\"}"
checks_json+=",{\"name\":\"task_completion\",\"result\":\"${task_result}\",\"detail\":\"${task_detail}\"}"
checks_json+=",{\"name\":\"spec_status\",\"result\":\"${status_result}\",\"detail\":\"${status_detail}\"}"
checks_json+=",{\"name\":\"unresolved_markers\",\"result\":\"${marker_result}\",\"detail\":\"${marker_detail}\"}"
checks_json+=",{\"name\":\"success_criteria\",\"result\":\"${sc_result}\",\"detail\":\"${sc_detail}\"}"
checks_json+="]"

markers_json=$(to_json_array "${markers[@]}")
sc_json=$(to_json_array "${sc_items[@]}")
fr_json=$(to_json_array "${fr_items[@]}")
incomplete_json=$(to_json_array "${incomplete_list[@]}")

cat <<EOF
{"overall":"${overall}","checks":${checks_json},"tasks":{"total":${total_tasks},"completed":${completed_tasks},"incomplete":${incomplete_tasks},"incomplete_list":${incomplete_json}},"status_field":"${status_field}","markers":${markers_json},"sc_items":${sc_json},"fr_items":${fr_json}}
EOF

exit 0
