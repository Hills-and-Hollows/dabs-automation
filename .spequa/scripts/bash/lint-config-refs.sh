#!/usr/bin/env bash
# lint-config-refs.sh — Validate <!-- config-refs: ... --> comments in command templates
# Ensures every referenced config key exists in the schema.
# Exit: 0 if all valid, 1 if any invalid keys found.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCHEMA="$REPO_ROOT/specs/006-layered-command-composition/contracts/config-schema.json"
TEMPLATES_DIR="$REPO_ROOT/templates/commands"

if [[ ! -f "$SCHEMA" ]]; then
    echo "ERROR: Schema not found at $SCHEMA" >&2
    exit 1
fi

# Extract valid keys from JSON schema properties
VALID_KEYS=$(grep -oE '"[a-z_]+":' "$SCHEMA" | sed 's/"//g;s/://' | sort -u)

errors=0

for template in "$TEMPLATES_DIR"/*.md; do
    filename=$(basename "$template")
    # Extract config-refs comment
    refs_line=$(grep -oP '(?<=<!-- config-refs: ).*?(?= -->)' "$template" 2>/dev/null || true)
    [[ -z "$refs_line" ]] && continue

    # Split by comma and validate each key
    IFS=',' read -ra keys <<< "$refs_line"
    for key in "${keys[@]}"; do
        key=$(echo "$key" | xargs)  # trim whitespace
        if ! echo "$VALID_KEYS" | grep -qx "$key"; then
            echo "ERROR: $filename references unknown config key '$key'" >&2
            errors=$((errors + 1))
        fi
    done
done

if [[ $errors -gt 0 ]]; then
    echo "$errors invalid config-ref(s) found" >&2
    exit 1
fi

echo "All config-refs valid"
