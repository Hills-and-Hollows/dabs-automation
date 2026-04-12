#!/usr/bin/env bash

# Pipeline scorecard generator
#
# Evaluates a completed pipeline run against 10 binary requirements (R1-R10)
# and generates a scorecard.md in the feature directory.
#
# Usage: ./generate-scorecard.sh --feature-dir <path> [--json]
#
# Flags:
#   --feature-dir <path>  Feature directory containing pipeline artifacts (required)
#   --json                Also emit JSON summary to stdout
#
# Exit code: Always 0 (caller interprets results)

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

# --- Parse arguments ---
FEATURE_DIR=""
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --feature-dir)
            FEATURE_DIR="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            echo "Usage: generate-scorecard.sh --feature-dir <path> [--json]" >&2
            exit 0
            ;;
    esac
done

if [[ -z "$FEATURE_DIR" ]]; then
    echo "ERROR: --feature-dir is required" >&2
    echo "Usage: generate-scorecard.sh --feature-dir <path> [--json]" >&2
    exit 0
fi

# Normalize to absolute path
if [[ ! "$FEATURE_DIR" = /* ]]; then
    FEATURE_DIR="$(cd "$FEATURE_DIR" && pwd)"
fi

# --- Load pipeline state ---
STATE_FILE="$FEATURE_DIR/.pipeline-state.json"
AUDIT_FILE="$FEATURE_DIR/audit-trail.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
TASKS_FILE="$FEATURE_DIR/tasks.md"

if [[ ! -f "$STATE_FILE" ]]; then
    echo "ERROR: .pipeline-state.json not found in $FEATURE_DIR" >&2
    exit 0
fi

# Read state file content once
STATE_CONTENT=$(cat "$STATE_FILE")

# Extract spec_id and feature_name from directory name
DIR_NAME=$(basename "$FEATURE_DIR")
SPEC_ID="${DIR_NAME%%-*}"
FEATURE_NAME="${DIR_NAME#*-}"

# Extract run_id from state (look for "run_id" field)
RUN_ID=$(echo "$STATE_CONTENT" | grep -o '"run_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"run_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "unknown")

# Current timestamp
COMPLETED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

# --- Helper: read a JSON field value (simple grep-based for portability) ---
json_field() {
    local field="$1"
    echo "$STATE_CONTENT" | grep -o "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/"
}

json_field_raw() {
    local field="$1"
    echo "$STATE_CONTENT" | grep -o "\"${field}\"[[:space:]]*:[[:space:]]*[^,}]*" | head -1 | sed "s/.*\"${field}\"[[:space:]]*:[[:space:]]*//"
}

# --- Requirement evaluation arrays ---
declare -a REQ_NAMES REQ_VERDICTS REQ_PROOFS REQ_DIAGNOSTICS

# --- R1: Autonomous Execution ---
# Audit trail exists and has no "manual transition" entries
r1_verdict="PASS"
r1_proof=""
r1_diag=""

if [[ ! -f "$AUDIT_FILE" ]]; then
    r1_verdict="FAIL"
    r1_proof="audit-trail.md not found"
    r1_diag="R1: audit-trail.md does not exist in $DIR_NAME"
elif grep -qi "manual transition" "$AUDIT_FILE" 2>/dev/null; then
    r1_verdict="FAIL"
    manual_count=$(grep -ci "manual transition" "$AUDIT_FILE" 2>/dev/null || echo "0")
    r1_proof="$manual_count manual transition(s) in audit trail"
    r1_diag="R1: Found $manual_count manual transition entries in audit-trail.md. Pipeline should execute autonomously."
else
    r1_proof="audit-trail.md present, no manual transitions"
fi

REQ_NAMES+=("Autonomous Execution")
REQ_VERDICTS+=("$r1_verdict")
REQ_PROOFS+=("$r1_proof")
REQ_DIAGNOSTICS+=("$r1_diag")

# --- R2: Spec Completeness ---
# spec.md has no TODO/TBD/placeholder markers, all sections present
r2_verdict="PASS"
r2_proof=""
r2_diag=""

if [[ ! -f "$SPEC_FILE" ]]; then
    r2_verdict="FAIL"
    r2_proof="spec.md not found"
    r2_diag="R2: spec.md does not exist in $DIR_NAME"
else
    # Check for TODO/TBD/placeholder markers (outside code blocks)
    marker_hits=()
    in_code=false
    line_num=0
    while IFS= read -r line; do
        line_num=$((line_num + 1))
        if [[ "$line" =~ ^\`\`\` ]]; then
            if $in_code; then in_code=false; else in_code=true; fi
            continue
        fi
        $in_code && continue
        stripped=$(echo "$line" | sed 's/`[^`]*`//g')
        if echo "$stripped" | grep -qiE '\bTODO\b|\bTBD\b|\[placeholder\]|\[NEEDS CLARIFICATION\]'; then
            marker_hits+=("L${line_num}")
        fi
    done < "$SPEC_FILE"

    if [[ ${#marker_hits[@]} -gt 0 ]]; then
        r2_verdict="FAIL"
        r2_proof="${#marker_hits[@]} unresolved marker(s) at ${marker_hits[*]}"
        r2_diag="R2: spec.md contains ${#marker_hits[@]} TODO/TBD/placeholder markers: ${marker_hits[*]}"
    else
        r2_proof="spec.md clean, no TODO/TBD/placeholder markers"
    fi
fi

REQ_NAMES+=("Spec Completeness")
REQ_VERDICTS+=("$r2_verdict")
REQ_PROOFS+=("$r2_proof")
REQ_DIAGNOSTICS+=("$r2_diag")

# --- R3: Decision Traceability ---
# All decisions in state have evidence or are human-resolved
r3_verdict="PASS"
r3_proof=""
r3_diag=""

# Look for decisions array in state; check each has evidence or resolution
if echo "$STATE_CONTENT" | grep -q '"decisions"'; then
    # Count decisions missing both evidence and resolution
    missing_evidence=$(echo "$STATE_CONTENT" | grep -o '"evidence"[[:space:]]*:[[:space:]]*""' | wc -l | tr -d ' ')
    missing_resolution=$(echo "$STATE_CONTENT" | grep -o '"resolution"[[:space:]]*:[[:space:]]*""' | wc -l | tr -d ' ')
    total_decisions=$(echo "$STATE_CONTENT" | grep -o '"decision_id"' | wc -l | tr -d ' ')

    if [[ "$total_decisions" -eq 0 ]]; then
        r3_proof="No decisions recorded in state"
    elif [[ "$missing_evidence" -gt 0 ]]; then
        r3_verdict="FAIL"
        r3_proof="$missing_evidence of $total_decisions decision(s) missing evidence"
        r3_diag="R3: $missing_evidence decision(s) lack evidence or human resolution in pipeline state"
    else
        r3_proof="All $total_decisions decision(s) have evidence or resolution"
    fi
else
    r3_proof="No decisions section in state (none required)"
fi

REQ_NAMES+=("Decision Traceability")
REQ_VERDICTS+=("$r3_verdict")
REQ_PROOFS+=("$r3_proof")
REQ_DIAGNOSTICS+=("$r3_diag")

# --- R4: AC Mapping ---
# tasks.md has AC mappings (grep for [US tags and [AC references)
r4_verdict="PASS"
r4_proof=""
r4_diag=""

if [[ ! -f "$TASKS_FILE" ]]; then
    r4_verdict="FAIL"
    r4_proof="tasks.md not found"
    r4_diag="R4: tasks.md does not exist in $DIR_NAME"
else
    us_count=$(grep -c '\[US' "$TASKS_FILE" 2>/dev/null || true)
    us_count="${us_count:-0}"
    us_count=$(echo "$us_count" | tr -d '[:space:]')
    ac_count=$(grep -c '\[AC' "$TASKS_FILE" 2>/dev/null || true)
    ac_count="${ac_count:-0}"
    ac_count=$(echo "$ac_count" | tr -d '[:space:]')

    if [[ "$us_count" -eq 0 && "$ac_count" -eq 0 ]]; then
        r4_verdict="FAIL"
        r4_proof="No [US or [AC references found in tasks.md"
        r4_diag="R4: tasks.md has no user story or acceptance criteria mappings. Tasks must trace to spec requirements."
    else
        r4_proof="${us_count} [US tag(s), ${ac_count} [AC reference(s)"
    fi
fi

REQ_NAMES+=("AC Mapping")
REQ_VERDICTS+=("$r4_verdict")
REQ_PROOFS+=("$r4_proof")
REQ_DIAGNOSTICS+=("$r4_diag")

# --- R5: Task Completion ---
# All tasks marked [x] in tasks.md, no TODO/FIXME in state
r5_verdict="PASS"
r5_proof=""
r5_diag=""

if [[ ! -f "$TASKS_FILE" ]]; then
    r5_verdict="FAIL"
    r5_proof="tasks.md not found"
    r5_diag="R5: tasks.md does not exist in $DIR_NAME"
else
    total_tasks=0
    completed_tasks=0
    incomplete_tasks=0

    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*-[[:space:]]\[[xX]\] ]]; then
            total_tasks=$((total_tasks + 1))
            completed_tasks=$((completed_tasks + 1))
        elif [[ "$line" =~ ^[[:space:]]*-[[:space:]]\[[[:space:]]\] ]]; then
            total_tasks=$((total_tasks + 1))
            incomplete_tasks=$((incomplete_tasks + 1))
        fi
    done < "$TASKS_FILE"

    state_todos=$(echo "$STATE_CONTENT" | grep -ciE '\bTODO\b|\bFIXME\b' 2>/dev/null || echo "0")

    if [[ "$incomplete_tasks" -gt 0 ]]; then
        r5_verdict="FAIL"
        r5_proof="$incomplete_tasks of $total_tasks task(s) incomplete"
        r5_diag="R5: $incomplete_tasks task(s) remain unchecked in tasks.md"
    elif [[ "$state_todos" -gt 0 ]]; then
        r5_verdict="FAIL"
        r5_proof="$state_todos TODO/FIXME marker(s) in pipeline state"
        r5_diag="R5: Pipeline state contains $state_todos TODO/FIXME markers"
    else
        r5_proof="$completed_tasks/$total_tasks tasks complete, no TODO/FIXME in state"
    fi
fi

REQ_NAMES+=("Task Completion")
REQ_VERDICTS+=("$r5_verdict")
REQ_PROOFS+=("$r5_proof")
REQ_DIAGNOSTICS+=("$r5_diag")

# --- R6: CI Gate ---
# State shows phase 7 (review) passed with gate_result=PASS
# Excluded when: phase 7 does not exist or was skipped (no CI configured)
r6_verdict="PASS"
r6_proof=""
r6_diag=""
r6_excluded=false

# Extract phase 7 (review) status from phases array
phase7_gate=""
phase7_status=""
if echo "$STATE_CONTENT" | grep -q '"name"[[:space:]]*:[[:space:]]*"review"'; then
    # Found review phase — extract its gate_result and status
    # Use awk to find the review phase block and extract fields
    phase7_gate=$(echo "$STATE_CONTENT" | tr ',' '\n' | grep -A1 '"name"[[:space:]]*:[[:space:]]*"review"' | grep -o '"gate_result"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
    phase7_status=$(echo "$STATE_CONTENT" | tr ',' '\n' | grep -A2 '"name"[[:space:]]*:[[:space:]]*"review"' | grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')

    if [[ "$phase7_status" == "skipped" ]]; then
        r6_excluded=true
        r6_verdict="EXCLUDED"
        r6_proof="Phase 7 (review) skipped - no CI configured"
    elif [[ "$phase7_gate" == "PASS" ]]; then
        r6_proof="Phase 7 gate_result=PASS"
    else
        r6_verdict="FAIL"
        r6_proof="Phase 7 (review) gate=${phase7_gate:-unknown}"
        r6_diag="R6: CI gate (phase 7) did not report gate_result=PASS"
    fi
else
    r6_excluded=true
    r6_verdict="EXCLUDED"
    r6_proof="No phase 7 (review) in pipeline state - no CI configured"
fi

REQ_NAMES+=("CI Gate")
REQ_VERDICTS+=("$r6_verdict")
REQ_PROOFS+=("$r6_proof")
REQ_DIAGNOSTICS+=("$r6_diag")

# --- R7: Review Gate ---
# State shows phase 7 passed
r7_verdict="PASS"
r7_proof=""
r7_diag=""

# Reuse phase7_status and phase7_gate from R6 check above
if [[ -n "$phase7_status" ]]; then
    if [[ "$phase7_status" == "completed" || "$phase7_status" == "passed" || "$phase7_gate" == "PASS" ]]; then
        r7_proof="Phase 7 (review) status=$phase7_status, gate=$phase7_gate"
    elif [[ "$phase7_status" == "skipped" ]]; then
        r7_verdict="FAIL"
        r7_proof="Phase 7 (review) was skipped"
        r7_diag="R7: Review phase was skipped — cannot verify 14-gate checklist"
    else
        r7_verdict="FAIL"
        r7_proof="Phase 7 (review) status=${phase7_status}"
        r7_diag="R7: Review phase did not complete successfully. Status: $phase7_status"
    fi
else
    r7_verdict="FAIL"
    r7_proof="No phase 7 (review) found in pipeline state"
    r7_diag="R7: Pipeline state has no review phase entry"
fi

REQ_NAMES+=("Review Gate")
REQ_VERDICTS+=("$r7_verdict")
REQ_PROOFS+=("$r7_proof")
REQ_DIAGNOSTICS+=("$r7_diag")

# --- R8: Deploy Gate ---
# State shows phase 8 (deploy) passed or deploy_target=none in config
r8_verdict="PASS"
r8_proof=""
r8_diag=""

deploy_target=$(json_field "deploy_target")
if [[ "$deploy_target" == "none" ]]; then
    r8_verdict="EXCLUDED"
    r8_proof="deploy_target=none in config"
elif echo "$STATE_CONTENT" | grep -q '"name"[[:space:]]*:[[:space:]]*"deploy"'; then
    phase8_gate=$(echo "$STATE_CONTENT" | tr ',' '\n' | grep -A1 '"name"[[:space:]]*:[[:space:]]*"deploy"' | grep -o '"gate_result"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
    phase8_status=$(echo "$STATE_CONTENT" | tr ',' '\n' | grep -A2 '"name"[[:space:]]*:[[:space:]]*"deploy"' | grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
    if [[ "$phase8_status" == "completed" || "$phase8_gate" == "PASS" ]]; then
        r8_proof="Phase 8 (deploy) status=$phase8_status"
    else
        r8_verdict="FAIL"
        r8_proof="Phase 8 (deploy) status=${phase8_status:-missing}"
        r8_diag="R8: Deploy phase did not complete successfully. Status: ${phase8_status:-not found}"
    fi
else
    r8_verdict="FAIL"
    r8_proof="No phase 8 (deploy) found in pipeline state"
    r8_diag="R8: Pipeline state has no deploy phase entry"
fi

REQ_NAMES+=("Deploy Gate")
REQ_VERDICTS+=("$r8_verdict")
REQ_PROOFS+=("$r8_proof")
REQ_DIAGNOSTICS+=("$r8_diag")

# --- R9: Retry Hygiene ---
# If retries exist in state, each has different strategy field
# Auto-PASS if no retries occurred
r9_verdict="PASS"
r9_proof=""
r9_diag=""

if echo "$STATE_CONTENT" | grep -q '"retries"\|"retry"'; then
    retry_count=$(echo "$STATE_CONTENT" | grep -o '"retry_id"\|"attempt"' | wc -l | tr -d ' ')
    if [[ "$retry_count" -gt 0 ]]; then
        # Check if strategies are duplicated
        strategies=$(echo "$STATE_CONTENT" | grep -o '"strategy"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | sort)
        unique_strategies=$(echo "$strategies" | sort -u)
        total_strats=$(echo "$strategies" | wc -l | tr -d ' ')
        unique_strats=$(echo "$unique_strategies" | wc -l | tr -d ' ')

        if [[ "$total_strats" -ne "$unique_strats" ]]; then
            r9_verdict="FAIL"
            r9_proof="$total_strats retries with only $unique_strats unique strategies"
            r9_diag="R9: Retries reused the same strategy. Each retry must use a different approach."
        else
            r9_proof="$retry_count retry(ies) with distinct strategies"
        fi
    else
        r9_proof="No retries occurred (auto-PASS)"
    fi
else
    r9_proof="No retries occurred (auto-PASS)"
fi

REQ_NAMES+=("Retry Hygiene")
REQ_VERDICTS+=("$r9_verdict")
REQ_PROOFS+=("$r9_proof")
REQ_DIAGNOSTICS+=("$r9_diag")

# --- R10: Audit Completeness ---
# audit-trail.md exists and has entries for completed phases
r10_verdict="PASS"
r10_proof=""
r10_diag=""

if [[ ! -f "$AUDIT_FILE" ]]; then
    r10_verdict="FAIL"
    r10_proof="audit-trail.md not found"
    r10_diag="R10: audit-trail.md does not exist in $DIR_NAME"
else
    audit_entries=$(grep -cE '^\s*##\s|^\s*\*\*Phase|^\|\s*[0-9]' "$AUDIT_FILE" 2>/dev/null || echo "0")
    if [[ "$audit_entries" -eq 0 ]]; then
        r10_verdict="FAIL"
        r10_proof="audit-trail.md has no phase entries"
        r10_diag="R10: audit-trail.md exists but contains no recognizable phase entries"
    else
        r10_proof="$audit_entries audit entry(ies) found"
    fi
fi

REQ_NAMES+=("Audit Completeness")
REQ_VERDICTS+=("$r10_verdict")
REQ_PROOFS+=("$r10_proof")
REQ_DIAGNOSTICS+=("$r10_diag")

# --- Scoring ---
pass_count=0
fail_count=0
excluded_count=0

for v in "${REQ_VERDICTS[@]}"; do
    case "$v" in
        PASS) pass_count=$((pass_count + 1)) ;;
        FAIL) fail_count=$((fail_count + 1)) ;;
        EXCLUDED) excluded_count=$((excluded_count + 1)) ;;
    esac
done

applicable=$((10 - excluded_count))
if [[ "$applicable" -gt 0 ]]; then
    score_pct=$((pass_count * 100 / applicable))
else
    score_pct=100
fi

# --- Determine verdict ---
THRESHOLD=80

if [[ "$fail_count" -eq 0 ]]; then
    VERDICT="PRODUCTION_READY"
elif [[ "$score_pct" -ge "$THRESHOLD" ]]; then
    VERDICT="CONDITIONAL_PASS"
elif [[ "$score_pct" -ge 50 ]]; then
    VERDICT="NEEDS_REMEDIATION"
else
    VERDICT="CRITICAL_FAILURE"
fi

# --- Extract execution summary metrics from state ---
total_duration=$(json_field "total_duration")
[[ -z "$total_duration" ]] && total_duration="N/A"

phases_completed=$(echo "$STATE_CONTENT" | grep -o '"status"[[:space:]]*:[[:space:]]*"completed"' | wc -l | tr -d '[:space:]')
total_phases=$(echo "$STATE_CONTENT" | grep -o '"name"[[:space:]]*:[[:space:]]*"[a-z]*"' | wc -l | tr -d '[:space:]')
[[ "$total_phases" -eq 0 ]] && total_phases="N/A"

# --- Generate scorecard.md ---
SCORECARD_PATH="$FEATURE_DIR/scorecard.md"

{
    echo "# Pipeline Scorecard: ${SPEC_ID}-${FEATURE_NAME}"
    echo ""
    echo "**Run ID**: ${RUN_ID}"
    echo "**Completed**: ${COMPLETED_AT}"
    echo "**Score**: ${pass_count}/${applicable}"
    echo "**Verdict**: ${VERDICT}"
    echo ""
    echo "## Requirements"
    echo ""
    echo "| # | Requirement | Verdict | Proof |"
    echo "|---|-------------|---------|-------|"

    for i in "${!REQ_NAMES[@]}"; do
        idx=$((i + 1))
        echo "| R${idx} | ${REQ_NAMES[$i]} | ${REQ_VERDICTS[$i]} | ${REQ_PROOFS[$i]} |"
    done

    echo ""
    echo "## Diagnostics"
    echo ""

    has_diag=false
    for i in "${!REQ_DIAGNOSTICS[@]}"; do
        if [[ -n "${REQ_DIAGNOSTICS[$i]}" ]]; then
            echo "- ${REQ_DIAGNOSTICS[$i]}"
            has_diag=true
        fi
    done
    if ! $has_diag; then
        echo "No failures detected."
    fi

    echo ""
    echo "## Execution Summary"
    echo ""
    echo "| Metric | Value |"
    echo "|--------|-------|"
    echo "| Total Duration | ${total_duration} |"
    echo "| Phases Completed | ${phases_completed}/${total_phases} |"
    echo "| Pass | ${pass_count} |"
    echo "| Fail | ${fail_count} |"
    echo "| Excluded | ${excluded_count} |"
    echo "| Score | ${score_pct}% |"
} > "$SCORECARD_PATH"

# --- JSON output ---
# Build requirements JSON array
to_json_array() {
    local arr=("$@")
    if [[ ${#arr[@]} -eq 0 ]]; then
        echo "[]"
        return
    fi
    local json="["
    local first=true
    for item in "${arr[@]}"; do
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

reqs_json="["
for i in "${!REQ_NAMES[@]}"; do
    idx=$((i + 1))
    [[ $i -gt 0 ]] && reqs_json+=","
    proof="${REQ_PROOFS[$i]//\\/\\\\}"
    proof="${proof//\"/\\\"}"
    reqs_json+="{\"id\":\"R${idx}\",\"name\":\"${REQ_NAMES[$i]}\",\"verdict\":\"${REQ_VERDICTS[$i]}\",\"proof\":\"${proof}\"}"
done
reqs_json+="]"

JSON_SUMMARY="{\"score\":\"${pass_count}/${applicable}\",\"verdict\":\"${VERDICT}\",\"scorecard_path\":\"${SCORECARD_PATH}\",\"requirements\":${reqs_json}}"

if $JSON_OUTPUT; then
    echo "$JSON_SUMMARY"
fi

exit 0
