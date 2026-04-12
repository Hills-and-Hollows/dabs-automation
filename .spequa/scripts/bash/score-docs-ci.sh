#!/bin/sh
# score-docs-ci.sh — Heuristic documentation quality checks for CI pipelines
# Usage: score-docs-ci.sh <file1.md> [file2.md] ...
# Exit: 0 = PASS (all files pass), 1 = FAIL (one or more files fail)
# Note: Full 5-dimension semantic scoring is agent-only (FR-012).
#       This script performs structural/heuristic checks only.

set -e

if [ $# -eq 0 ]; then
  echo "Usage: score-docs-ci.sh <file1.md> [file2.md] ..."
  echo "No files provided — nothing to check."
  exit 0
fi

OVERALL_PASS=true
FINDINGS=""

for DOC in "$@"; do
  if [ ! -f "$DOC" ]; then
    FINDINGS="${FINDINGS}\n## ${DOC}\n- SKIP: File does not exist\n"
    continue
  fi

  FILE_PASS=true
  FILE_FINDINGS=""

  # Check 1: Dead internal markdown links
  # Extract [text](path) links that point to local files (not http/https)
  DEAD_LINKS=""
  DOC_DIR=$(dirname "$DOC")
  while IFS= read -r link; do
    # Skip anchor-only links
    case "$link" in
      \#*) continue ;;
    esac
    # Resolve relative to doc directory
    TARGET="${DOC_DIR}/${link}"
    # Strip anchor from path
    TARGET_PATH=$(echo "$TARGET" | sed 's/#.*//')
    if [ -n "$TARGET_PATH" ] && [ ! -e "$TARGET_PATH" ]; then
      DEAD_LINKS="${DEAD_LINKS}\n  - Dead link: [${link}]"
      FILE_PASS=false
    fi
  done <<EOF
$(grep -oE '\[([^]]*)\]\(([^)]+)\)' "$DOC" | grep -oE '\(([^)]+)\)' | sed 's/^(//;s/)$//' | grep -v '^http' | grep -v '^mailto')
EOF

  if [ -n "$DEAD_LINKS" ]; then
    FILE_FINDINGS="${FILE_FINDINGS}\n- Dead links found:${DEAD_LINKS}"
  fi

  # Check 2: Required sections present (for known doc types)
  BASENAME=$(basename "$DOC")
  case "$BASENAME" in
    README.md)
      for section in "## " "# "; do
        if ! grep -q "^${section}" "$DOC" 2>/dev/null; then
          FILE_FINDINGS="${FILE_FINDINGS}\n- Missing headings: No ${section} heading found"
          FILE_PASS=false
          break
        fi
      done
      ;;
    CHANGELOG.md)
      if ! grep -qE '^\#\#? ' "$DOC" 2>/dev/null; then
        FILE_FINDINGS="${FILE_FINDINGS}\n- Missing version headings in CHANGELOG"
        FILE_PASS=false
      fi
      ;;
  esac

  # Check 3: Stale references — code snippets reference existing files
  while IFS= read -r ref_path; do
    if [ -n "$ref_path" ] && [ ! -e "$ref_path" ]; then
      FILE_FINDINGS="${FILE_FINDINGS}\n- Stale reference: \`${ref_path}\` does not exist"
      FILE_PASS=false
    fi
  done <<EOF
$(grep -oE '`(src/[^`]+|scripts/[^`]+|templates/[^`]+|docs/[^`]+)`' "$DOC" | sed 's/^`//;s/`$//' 2>/dev/null || true)
EOF

  # Check 4: Unresolved placeholders (exclude backtick-quoted references)
  # Strip inline code (`...`) before checking for placeholders to avoid false positives
  # when docs describe the marker system itself (e.g., "use `[NEEDS CLARIFICATION]` markers")
  if sed 's/`[^`]*`//g' "$DOC" | grep -qE '\[NEEDS CLARIFICATION\]|\[TODO\]|\[TBD\]|\[PLACEHOLDER\]|TKTK' 2>/dev/null; then
    FILE_FINDINGS="${FILE_FINDINGS}\n- Unresolved placeholders found"
    FILE_PASS=false
  fi

  # Build per-file report
  if [ "$FILE_PASS" = true ]; then
    FINDINGS="${FINDINGS}\n## ${DOC}\n- PASS: All heuristic checks passed\n"
  else
    FINDINGS="${FINDINGS}\n## ${DOC}\n- FAIL:${FILE_FINDINGS}\n"
    OVERALL_PASS=false
  fi
done

# Output report
echo "# Documentation Quality Check (CI)"
echo ""
if [ "$OVERALL_PASS" = true ]; then
  echo "**Result**: PASS"
else
  echo "**Result**: FAIL"
fi
echo ""
printf "%b" "$FINDINGS"

if [ "$OVERALL_PASS" = true ]; then
  exit 0
else
  exit 1
fi
