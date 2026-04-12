#!/usr/bin/env pwsh

# Concurrency lock management for SDD pipeline runs (PowerShell parity)
#
# Checks .pipeline-state.json for active locks to prevent two
# pipeline runs from executing simultaneously against the same repo.
#
# Usage: ./check-concurrent-runs.ps1 [-Json] [-Status] [-FeatureDir <path>]
#
# Exit codes:
#   0 = no conflict (safe to proceed)
#   1 = locked (active pipeline run in progress)

param(
    [switch]$Json,
    [switch]$Status,
    [string]$FeatureDir
)

# --- Resolve feature directory ---
if ($FeatureDir) {
    $resolvedDir = $FeatureDir
} else {
    # Auto-detect from git branch
    $repoRoot = if (git rev-parse --show-toplevel 2>$null) {
        git rev-parse --show-toplevel
    } else {
        $PSScriptRoot | Split-Path | Split-Path | Split-Path
    }

    $currentBranch = if ($env:SPEQUAFY_FEATURE) {
        $env:SPEQUAFY_FEATURE
    } elseif (git rev-parse --abbrev-ref HEAD 2>$null) {
        git rev-parse --abbrev-ref HEAD
    } else {
        'main'
    }

    # Extract numeric prefix and find matching spec directory
    $specsDir = Join-Path $repoRoot 'specs'
    if ($currentBranch -match '^(\d{3})-' -and (Test-Path $specsDir)) {
        $prefix = $Matches[1]
        $matches_ = Get-ChildItem -Path $specsDir -Directory -Filter "$prefix-*" 2>$null
        if ($matches_.Count -eq 1) {
            $resolvedDir = $matches_[0].FullName
        } else {
            $resolvedDir = Join-Path $specsDir $currentBranch
        }
    } else {
        $resolvedDir = Join-Path $specsDir $currentBranch
    }
}

# Normalize to absolute path
if (-not [System.IO.Path]::IsPathRooted($resolvedDir)) {
    try {
        $resolvedDir = (Resolve-Path $resolvedDir -ErrorAction Stop).Path
    } catch {
        Write-Output '{"locked":false,"message":"Feature directory not found"}'
        exit 0
    }
}

$stateFile = Join-Path $resolvedDir '.pipeline-state.json'

# --- Check if state file exists ---
if (-not (Test-Path $stateFile)) {
    Write-Output '{"locked":false,"message":"No pipeline state found"}'
    exit 0
}

# --- Read lock fields from state file ---
try {
    $state = Get-Content $stateFile -Raw | ConvertFrom-Json
} catch {
    Write-Output '{"locked":false,"message":"Invalid pipeline state file"}'
    exit 0
}

$lockPid = $null
$lockAcquired = $null

if ($state.PSObject.Properties['lock'] -and $state.lock) {
    if ($state.lock.PSObject.Properties['pid']) {
        $lockPid = $state.lock.pid
    }
    if ($state.lock.PSObject.Properties['acquired_at']) {
        $lockAcquired = $state.lock.acquired_at
    }
}

# --- No lock set ---
if ($null -eq $lockPid) {
    Write-Output '{"locked":false,"message":"No active lock"}'
    exit 0
}

# --- Lock exists: check if PID is alive ---
$processAlive = $false
try {
    $proc = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
    if ($proc) {
        $processAlive = $true
    }
} catch {
    $processAlive = $false
}

if ($processAlive) {
    # Process is alive - pipeline run in progress
    Write-Output "{`"locked`":true,`"pid`":$lockPid,`"acquired_at`":`"$lockAcquired`",`"message`":`"Pipeline run in progress`"}"
    exit 1
} else {
    # Process is dead - stale lock
    if (-not $Status) {
        # Clear the stale lock
        $state.lock.pid = $null
        $state.lock.acquired_at = $null
        $state | ConvertTo-Json -Depth 10 | Set-Content $stateFile -NoNewline
    }

    Write-Output "{`"locked`":false,`"stale`":true,`"old_pid`":$lockPid,`"message`":`"Stale lock cleared`"}"
    exit 0
}
