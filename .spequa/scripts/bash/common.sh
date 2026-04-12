#!/usr/bin/env bash
# Common functions and variables for all scripts

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPEQUAFY_FEATURE environment variable is set
    if [[ -n "${SPEQUAFY_FEATURE:-}" ]]; then
        echo "$SPEQUAFY_FEATURE"
        return
    fi

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local config_spec_dir=""
    if [[ -f "$repo_root/.spequa/config.yml" ]]; then
        config_spec_dir=$(sed -n 's/^spec_dir:[[:space:]]*//p' "$repo_root/.spequa/config.yml" | head -1 | sed "s/^[\"']//;s/[\"']$//")
    fi
    local specs_dir="$repo_root/${config_spec_dir:-specs}"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi

    echo "main"  # Final fallback
}

# Check if we have git available
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[spequafy] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    # Support optional branch_prefix from config (e.g., "feat/" → "feat/001-feature")
    local bp
    bp=$(spequa_config "branch_prefix" "")
    local pattern="^${bp}[0-9]{3}-"
    if [[ ! "$branch" =~ $pattern ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        if [[ -n "$bp" ]]; then
            echo "Feature branches should be named like: ${bp}001-feature-name" >&2
        else
            echo "Feature branches should be named like: 001-feature-name" >&2
        fi
        return 1
    fi

    return 0
}

get_feature_dir() {
    local repo_root="$1" branch="$2"
    local sd
    sd=$(spequa_config "spec_dir" "specs")
    echo "$repo_root/$sd/$branch"
}

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local sd
    sd=$(spequa_config "spec_dir" "specs")
    local specs_dir="$repo_root/$sd"

    # Strip branch_prefix if present (e.g., "feat/004-whatever" → "004-whatever")
    local bp
    bp=$(spequa_config "branch_prefix" "")
    if [[ -n "$bp" ]] && [[ "$branch_name" == "${bp}"* ]]; then
        branch_name="${branch_name#"$bp"}"
    fi

    # Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    if [[ ! "$branch_name" =~ ^([0-9]{3})- ]]; then
        # If branch doesn't have numeric prefix, fall back to exact match
        echo "$specs_dir/$branch_name"
        return
    fi

    local prefix="${BASH_REMATCH[1]}"

    # Search for directories in specs/ that start with this prefix
    local matches=()
    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/"$prefix"-*; do
            if [[ -d "$dir" ]]; then
                matches+=("$(basename "$dir")")
            fi
        done
    fi

    # Handle results
    if [[ ${#matches[@]} -eq 0 ]]; then
        # No match found - return the branch name path (will fail later with clear error)
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        # Exactly one match - perfect!
        echo "$specs_dir/${matches[0]}"
    else
        # Multiple matches - this shouldn't happen with proper naming convention
        echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
        echo "Please ensure only one spec directory exists per numeric prefix." >&2
        echo "$specs_dir/$branch_name"  # Return something to avoid breaking the script
    fi
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # Use prefix-based lookup to support multiple branches per spec
    local feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")

    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/spec.md'
IMPL_PLAN='$feature_dir/plan.md'
TASKS='$feature_dir/tasks.md'
RESEARCH='$feature_dir/research.md'
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/quickstart.md'
CONTRACTS_DIR='$feature_dir/contracts'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

# ── Config System (spec 006) ──────────────────────────────────────────────

# Known config keys and their default values
_EQUASPEC_CONFIG_KEYS="primary test_command package_manager branch_prefix project_root spec_dir custom_scripts custom"

# Read a single value from .spequa/config.yml with a fallback default.
# Usage: spequa_config "key" "default_value"
# Returns: the configured value, or default if config missing/key absent.
spequa_config() {
    local key="$1"
    local default_val="${2:-}"
    local repo_root
    repo_root="$(get_repo_root)"
    local config_file="$repo_root/.spequa/config.yml"

    if [[ ! -f "$config_file" ]]; then
        echo "$default_val"
        return
    fi

    # Simple YAML parser: match top-level "key: value" lines.
    # Handles quoted and unquoted values. Does not parse nested maps.
    local value
    value=$(sed -n "s/^${key}:[[:space:]]*//p" "$config_file" | head -1)

    if [[ -z "$value" ]]; then
        echo "$default_val"
        return
    fi

    # Strip surrounding quotes (single or double)
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"

    echo "$value"
}

# Validate .spequa/config.yml against known keys.
# Warns on unrecognized keys with Levenshtein-based suggestions.
# Warns on path-valued keys that reference missing files/directories.
spequa_validate_config() {
    local repo_root
    repo_root="$(get_repo_root)"
    local config_file="$repo_root/.spequa/config.yml"

    if [[ ! -f "$config_file" ]]; then
        return 0
    fi

    # Extract top-level keys (lines matching "key:" at start, excluding comments)
    local found_keys
    found_keys=$(grep -E '^[a-zA-Z_][a-zA-Z0-9_]*:' "$config_file" | sed 's/:.*//')

    local valid=0
    while IFS= read -r key; do
        [[ -z "$key" ]] && continue
        local is_known=false
        for known in $_EQUASPEC_CONFIG_KEYS; do
            if [[ "$key" == "$known" ]]; then
                is_known=true
                break
            fi
        done

        if [[ "$is_known" == false ]]; then
            local suggestion
            suggestion=$(_spequa_suggest_key "$key")
            if [[ -n "$suggestion" ]]; then
                echo "[config] Warning: Unknown key '$key' in .spequa/config.yml — did you mean '$suggestion'?" >&2
            else
                echo "[config] Warning: Unknown key '$key' in .spequa/config.yml" >&2
            fi
            valid=1
        fi
    done <<< "$found_keys"

    # Validate path-valued keys: project_root must exist
    local project_root
    project_root=$(spequa_config "project_root" ".")
    if [[ "$project_root" != "." ]] && [[ ! -d "$repo_root/$project_root" ]]; then
        echo "[config] Warning: project_root '$project_root' does not exist (expected at $repo_root/$project_root)" >&2
        valid=1
    fi

    # Validate custom_scripts paths
    # Parse custom_scripts block: lines indented under custom_scripts: with key: value
    local in_custom_scripts=false
    while IFS= read -r line; do
        if [[ "$line" =~ ^custom_scripts: ]]; then
            in_custom_scripts=true
            continue
        fi
        if [[ "$in_custom_scripts" == true ]]; then
            # Stop at next top-level key
            if [[ "$line" =~ ^[a-zA-Z_] ]] && [[ ! "$line" =~ ^[[:space:]] ]]; then
                break
            fi
            # Parse indented key: value
            if [[ "$line" =~ ^[[:space:]]+([a-zA-Z_]+):[[:space:]]*(.+) ]]; then
                local script_key="${BASH_REMATCH[1]}"
                local script_path="${BASH_REMATCH[2]}"
                # Strip quotes
                script_path="${script_path#\"}"
                script_path="${script_path%\"}"
                script_path="${script_path#\'}"
                script_path="${script_path%\'}"
                if [[ -n "$script_path" ]] && [[ ! -f "$repo_root/$script_path" ]]; then
                    echo "[config] Warning: custom_scripts.$script_key references '$script_path' which does not exist (expected at $repo_root/$script_path)" >&2
                    valid=1
                fi
            fi
        fi
    done < "$config_file"

    return $valid
}

# Compute Levenshtein distance between two strings (pure bash).
_spequa_levenshtein() {
    local s="$1" t="$2"
    local s_len=${#s} t_len=${#t}

    # Quick checks
    [[ "$s" == "$t" ]] && echo 0 && return
    [[ $s_len -eq 0 ]] && echo "$t_len" && return
    [[ $t_len -eq 0 ]] && echo "$s_len" && return

    # Use single array for space efficiency
    local -a row
    for ((j = 0; j <= t_len; j++)); do
        row[$j]=$j
    done

    for ((i = 1; i <= s_len; i++)); do
        local prev=$((i - 1))
        row[0]=$i
        for ((j = 1; j <= t_len; j++)); do
            local cost=0
            [[ "${s:$((i-1)):1}" != "${t:$((j-1)):1}" ]] && cost=1
            local del=$((row[j] + 1))
            local ins=$((row[j-1] + 1))
            local sub=$((prev + cost))
            prev=${row[$j]}
            # min of del, ins, sub
            local min=$del
            [[ $ins -lt $min ]] && min=$ins
            [[ $sub -lt $min ]] && min=$sub
            row[$j]=$min
        done
    done

    echo "${row[$t_len]}"
}

# Find the closest known key to an unknown key (within distance 2).
_spequa_suggest_key() {
    local unknown="$1"
    local best_key=""
    local best_dist=3  # Only suggest if distance <= 2

    for known in $_EQUASPEC_CONFIG_KEYS; do
        local dist
        dist=$(_spequa_levenshtein "$unknown" "$known")
        if [[ $dist -lt $best_dist ]]; then
            best_dist=$dist
            best_key=$known
        fi
    done

    echo "$best_key"
}

