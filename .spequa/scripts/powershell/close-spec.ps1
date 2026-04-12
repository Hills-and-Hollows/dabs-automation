#!/usr/bin/env pwsh

# Close spec helper script (PowerShell)
#
# Locates a spec directory by number, verifies the implementing PR is merged,
# and outputs JSON with paths and merge metadata for the closure workflow.
#
# Usage: ./close-spec.ps1 [OPTIONS] <spec-number>
#
# OPTIONS:
#   -Json               Output in JSON format
#   -Help               Show help message
#
# ARGUMENTS:
#   <spec-number>       Spec number (e.g., 005) or full directory name (e.g., 005-spec-closure)

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: close-spec.ps1 [OPTIONS] <spec-number>

Locate a spec directory and verify its implementing PR is merged.

OPTIONS:
  -Json               Output in JSON format
  -Help               Show this help message

ARGUMENTS:
  <spec-number>       Spec number (e.g., 005) or full name (e.g., 005-spec-closure)

EXAMPLES:
  # Close spec 005
  .\close-spec.ps1 -Json 005

  # Close by full name
  .\close-spec.ps1 -Json 005-spec-closure

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Extract spec input from arguments
$SpecInput = ''
foreach ($arg in $Arguments) {
    if ($arg -and $arg -notmatch '^-') {
        $SpecInput = $arg
        break
    }
}

if (-not $SpecInput) {
    Write-Error 'Spec number or name is required. Usage: close-spec.ps1 [-Json] <spec-number>'
    exit 1
}

# Get repository root
$RepoRoot = Get-RepoRoot
$SpecsDir = Join-Path $RepoRoot 'specs'

# Default branch (prefer gh, else origin/HEAD, else main)
$DefaultBranch = 'main'
try {
    Push-Location $RepoRoot
    $db = gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>$null
    if ($db) { $DefaultBranch = $db }
} catch {
    try {
        $orig = git symbolic-ref refs/remotes/origin/HEAD 2>$null
        if ($orig -match 'refs/remotes/origin/(.+)$') { $DefaultBranch = $Matches[1] }
    } catch { }
} finally {
    Pop-Location
}

# Extract numeric prefix
if ($SpecInput -match '^(\d{3})') {
    $Prefix = $Matches[1]
} else {
    Write-Error "Invalid spec identifier '$SpecInput'. Expected format: NNN or NNN-feature-name"
    exit 1
}

# Find spec directory by prefix
$MatchDirs = @()
if (Test-Path $SpecsDir) {
    $MatchDirs = Get-ChildItem -Path $SpecsDir -Directory -Filter "$Prefix-*"
}

if ($MatchDirs.Count -eq 0) {
    Write-Error "No spec directory found with prefix '$Prefix' in $SpecsDir"
    exit 1
}

if ($MatchDirs.Count -gt 1) {
    Write-Error "Multiple spec directories found with prefix '$Prefix'. Please use the full name."
    exit 1
}

$SpecDir = $MatchDirs[0].FullName
$SpecFile = Join-Path $SpecDir 'spec.md'
$SpecName = $MatchDirs[0].Name

if (-not (Test-Path $SpecFile)) {
    Write-Error "spec.md not found in $SpecDir"
    exit 1
}

# Check for baseline-tests.md
$BaselineFile = Join-Path $SpecDir 'baseline-tests.md'
if (-not (Test-Path $BaselineFile)) {
    $BaselineFile = ''
}

# Check PR merge status via gh CLI
$PrUrl = ''
$MergeDate = ''
$PrMerged = $false

try {
    $PrData = gh pr list --state merged --search $Prefix --json url,mergedAt --limit 5 2>$null | ConvertFrom-Json
    if ($PrData -and $PrData.Count -gt 0) {
        $PrUrl = $PrData[0].url
        $MergeDate = ($PrData[0].mergedAt).ToString('yyyy-MM-dd')
        $PrMerged = $true
    }
} catch {
    # gh not available or failed — fall through to git check
}

# Merge commit on base branch (requires gh + real PR URL)
$MergeCommit = ''
if ($PrUrl -match '^https?://') {
    try {
        $MergeCommit = gh pr view $PrUrl --json mergeCommit --jq '.mergeCommit.oid' 2>$null
    } catch {
        $MergeCommit = ''
    }
}

# Fallback: check git log for merge evidence
if (-not $PrMerged) {
    try {
        $GitLog = git log --oneline main 2>$null
        if ($GitLog -match $Prefix) {
            $PrMerged = $true
            $MergeDate = (Get-Date).ToString('yyyy-MM-dd')
            $PrUrl = '(detected via git log, no gh CLI PR match)'
        }
    } catch {
        # Git not available
    }
}

# Output results
if ($Json) {
    [PSCustomObject]@{
        SPEC_DIR        = $SpecDir
        SPEC_FILE       = $SpecFile
        SPEC_NAME       = $SpecName
        PR_URL          = $PrUrl
        MERGE_DATE      = $MergeDate
        BASELINE_FILE   = $BaselineFile
        PR_MERGED       = $PrMerged
        MERGE_COMMIT    = $MergeCommit
        DEFAULT_BRANCH  = $DefaultBranch
    } | ConvertTo-Json -Compress
} else {
    Write-Output "SPEC_DIR: $SpecDir"
    Write-Output "SPEC_FILE: $SpecFile"
    Write-Output "SPEC_NAME: $SpecName"
    Write-Output "PR_URL: $(if ($PrUrl) { $PrUrl } else { 'N/A' })"
    Write-Output "MERGE_DATE: $(if ($MergeDate) { $MergeDate } else { 'N/A' })"
    Write-Output "BASELINE_FILE: $(if ($BaselineFile) { $BaselineFile } else { 'N/A' })"
    Write-Output "PR_MERGED: $PrMerged"
    Write-Output "MERGE_COMMIT: $(if ($MergeCommit) { $MergeCommit } else { 'N/A' })"
    Write-Output "DEFAULT_BRANCH: $DefaultBranch"
}
