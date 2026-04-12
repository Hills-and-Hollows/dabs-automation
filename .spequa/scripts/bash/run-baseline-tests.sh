#!/bin/sh
# run-baseline-tests.sh — Run project test suite and output structured Markdown baseline
# Usage: run-baseline-tests.sh [project-root]
# Output: Markdown per contracts/baseline-tests-format.md on stdout
# Exit: 0 always (caller decides how to handle results)

set -e

PROJECT_ROOT="${1:-.}"
cd "$PROJECT_ROOT"

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
CAPTURED=$(date '+%Y-%m-%d %H:%M')
TIMEOUT=60

# Read config value from .spequa/config.yml with fallback default (POSIX sh).
_read_config() {
  _key="$1"; _default="$2"
  _config_file=".spequa/config.yml"
  if [ ! -f "$_config_file" ]; then echo "$_default"; return; fi
  _val=$(sed -n "s/^${_key}:[[:space:]]*//p" "$_config_file" | head -1)
  if [ -z "$_val" ]; then echo "$_default"; return; fi
  # Strip surrounding quotes
  _val=$(echo "$_val" | sed "s/^[\"']//;s/[\"']$//")
  echo "$_val"
}

# Resolve test command and runner name from config (spec 006)
TEST_COMMAND=$(_read_config "test_command" "uv run pytest --tb=short -q")
PKG_MANAGER=$(_read_config "package_manager" "uv")

# Extract runner name from test command for display (first recognizable tool)
case "$TEST_COMMAND" in
  *pytest*) RUNNER="pytest" ;;
  *jest*)   RUNNER="jest" ;;
  *vitest*) RUNNER="vitest" ;;
  *cargo\ test*) RUNNER="cargo-test" ;;
  *go\ test*)    RUNNER="go-test" ;;
  *mvn\ test*)   RUNNER="maven" ;;
  *npm\ test*)   RUNNER="npm-test" ;;
  *) RUNNER="custom" ;;
esac

# Check if the package manager / test tool is available
# Extract the first word of the test command as the executable to check
TEST_EXEC=$(echo "$TEST_COMMAND" | awk '{print $1}')
if ! command -v "$TEST_EXEC" >/dev/null 2>&1; then
  cat <<EOF
# Baseline Test Results

**Captured**: ${CAPTURED} | **Branch**: ${BRANCH} | **Runner**: ${RUNNER}

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | 0      |
| Passed     | 0      |
| Failed     | 0      |
| Skipped    | 0      |
| Status     | SKIP   |

> Test runner not available (${TEST_EXEC} not found in PATH).
EOF
  exit 0
fi

# Run pytest with timeout
TMPFILE=$(mktemp)
TMPFILE_ERR=$(mktemp)
trap 'rm -f "$TMPFILE" "$TMPFILE_ERR"' EXIT

# Use timeout command if available, otherwise use shell background + wait
if command -v timeout >/dev/null 2>&1; then
  timeout "${TIMEOUT}" $TEST_COMMAND 2>"$TMPFILE_ERR" >"$TMPFILE" || true
elif command -v gtimeout >/dev/null 2>&1; then
  gtimeout "${TIMEOUT}" $TEST_COMMAND 2>"$TMPFILE_ERR" >"$TMPFILE" || true
else
  # Fallback: run in background with manual timeout
  $TEST_COMMAND 2>"$TMPFILE_ERR" >"$TMPFILE" &
  PID=$!
  ELAPSED=0
  while kill -0 "$PID" 2>/dev/null; do
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
      kill "$PID" 2>/dev/null || true
      wait "$PID" 2>/dev/null || true
      cat <<EOF
# Baseline Test Results

**Captured**: ${CAPTURED} | **Branch**: ${BRANCH} | **Runner**: ${RUNNER}

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | 0      |
| Passed     | 0      |
| Failed     | 0      |
| Skipped    | 0      |
| Status     | SKIP   |

> Test suite exceeded ${TIMEOUT}-second timeout.
EOF
      exit 0
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
  done
  wait "$PID" 2>/dev/null || true
fi

OUTPUT=$(cat "$TMPFILE")

# Check for timeout exit code (124 from timeout/gtimeout)
if [ ! -s "$TMPFILE" ] && grep -qi "no tests ran\|no module named\|error" "$TMPFILE_ERR" 2>/dev/null; then
  cat <<EOF
# Baseline Test Results

**Captured**: ${CAPTURED} | **Branch**: ${BRANCH} | **Runner**: ${RUNNER}

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | 0      |
| Passed     | 0      |
| Failed     | 0      |
| Skipped    | 0      |
| Status     | SKIP   |

> No tests found or test framework error.
EOF
  exit 0
fi

# Parse pytest short summary line: "X passed, Y failed, Z skipped"
# The summary line is typically the last non-empty line
SUMMARY_LINE=$(echo "$OUTPUT" | grep -E '[0-9]+ passed|[0-9]+ failed|[0-9]+ skipped|[0-9]+ error' | tail -1)

PASSED=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
FAILED=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
SKIPPED=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' || echo "0")
ERRORS=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' || echo "0")

# Default to 0 if empty
PASSED=${PASSED:-0}
FAILED=${FAILED:-0}
SKIPPED=${SKIPPED:-0}
ERRORS=${ERRORS:-0}

TOTAL=$((PASSED + FAILED + SKIPPED + ERRORS))

# Determine status
if [ "$TOTAL" -eq 0 ]; then
  STATUS="SKIP"
elif [ "$FAILED" -gt 0 ] || [ "$ERRORS" -gt 0 ]; then
  STATUS="WARN"
else
  STATUS="PASS"
fi

# Check for coverage in output
COVERAGE=$(echo "$OUTPUT" | grep -oE 'TOTAL[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9.]+%' | grep -oE '[0-9.]+%' || echo "")

# Output baseline Markdown
cat <<EOF
# Baseline Test Results

**Captured**: ${CAPTURED} | **Branch**: ${BRANCH} | **Runner**: ${RUNNER}

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | ${TOTAL} |
| Passed     | ${PASSED} |
| Failed     | ${FAILED} |
| Skipped    | ${SKIPPED} |
EOF

# Only include coverage row if available
if [ -n "$COVERAGE" ]; then
  cat <<EOF
| Coverage   | ${COVERAGE} |
EOF
fi

cat <<EOF
| Status     | ${STATUS} |
EOF

# Include failure details if any
if [ "$STATUS" = "WARN" ]; then
  echo ""
  echo "## Failures"
  echo ""
  # Extract FAILED/ERROR lines from pytest output (lines before the summary)
  echo "$OUTPUT" | grep -E "^FAILED |^ERROR " | while IFS= read -r line; do
    TEST_NAME=$(echo "$line" | sed 's/^FAILED //;s/^ERROR //;s/ - .*$//')
    echo "### ${TEST_NAME}"
    echo ""
    echo '```'
    echo "$line"
    echo '```'
    echo ""
  done
fi
