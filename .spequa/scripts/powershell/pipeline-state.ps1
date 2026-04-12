#!/usr/bin/env pwsh

# CRUD operations for .pipeline-state.json in a spec feature directory.
#
# Usage: ./pipeline-state.ps1 <subcommand> [options]
#
# Subcommands:
#   init     Create a new .pipeline-state.json
#   read     Output current pipeline state
#   update   Update phase, status, or artifact entries
#   lock     Acquire PID-based lock
#   unlock   Release lock
#
# Exit code: 0 on success, 1 on error

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('init', 'read', 'update', 'lock', 'unlock')]
    [string]$Subcommand,

    [switch]$Json,

    [string]$FeatureDir,

    # init options
    [string]$SpecId,
    [string]$FeatureName,
    [string]$AutonomyLevel = 'HIGH',
    [int]$Timeout = 60,
    [string]$DeployTarget = 'none',
    [int]$ScoreThreshold = 10,

    # update options
    [int]$Phase = -1,
    [string]$PhaseStatus,
    [string]$GateResult,
    [string]$Status,
    [string]$AddArtifact
)

$ErrorActionPreference = 'Stop'
$StateFileName = '.pipeline-state.json'

# --- Helpers ---

function Get-Iso8601Now {
    (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
}

function Get-UnixTimestamp {
    [int][double]::Parse((Get-Date -UFormat '%s'))
}

function Resolve-FeatureDir {
    param([string]$Override)

    if ($Override) {
        if (-not [System.IO.Path]::IsPathRooted($Override)) {
            return (Resolve-Path $Override).Path
        }
        return $Override
    }

    # Auto-detect from git
    $repoRoot = $null
    try {
        $repoRoot = (git rev-parse --show-toplevel 2>$null)
    } catch {}

    if (-not $repoRoot) {
        $scriptDir = Split-Path -Parent $MyInvocation.ScriptName
        $repoRoot = (Resolve-Path (Join-Path $scriptDir '../../..')).Path
    }

    $branch = $null
    if ($env:SPEQUAFY_FEATURE) {
        $branch = $env:SPEQUAFY_FEATURE
    } else {
        try {
            $branch = (git rev-parse --abbrev-ref HEAD 2>$null)
        } catch {}
    }

    if (-not $branch) { $branch = 'main' }

    $specsDir = Join-Path $repoRoot 'specs'

    # Extract numeric prefix
    if ($branch -match '^(\d{3})-') {
        $prefix = $Matches[1]
        $matches_found = @()
        if (Test-Path $specsDir) {
            $matches_found = Get-ChildItem -Path $specsDir -Directory -Filter "$prefix-*"
        }
        if ($matches_found.Count -eq 1) {
            return $matches_found[0].FullName
        }
    }

    return Join-Path $specsDir $branch
}

function Write-ErrorJson {
    param([string]$Message)
    Write-Error "{`"error`":`"$Message`"}"
    exit 1
}

function Get-StatePath {
    param([string]$Dir)
    Join-Path $Dir $StateFileName
}

# --- Subcommands ---

function Invoke-Init {
    param([string]$FDir)

    $dirName = Split-Path -Leaf $FDir

    # Auto-detect spec_id
    $sid = $SpecId
    if (-not $sid -and $dirName -match '^(\d{3})-') {
        $sid = $Matches[1]
    }

    # Auto-detect feature_name
    $fname = $FeatureName
    if (-not $fname) { $fname = $dirName }

    $ts = Get-UnixTimestamp
    $runId = "$sid-$ts"
    $now = Get-Iso8601Now
    $filePath = Get-StatePath $FDir

    $state = [ordered]@{
        schema_version = '1.0'
        run_id         = $runId
        spec_id        = $sid
        feature_name   = $fname
        status         = 'running'
        started_at     = $now
        completed_at   = $null
        config         = [ordered]@{
            autonomy_level       = $AutonomyLevel
            max_retries_per_phase = 3
            timeout_minutes      = $Timeout
            target_repo          = ''
            branch_from          = 'main'
            deploy_target        = $DeployTarget
            score_threshold      = $ScoreThreshold
            pause_on_destructive = $true
        }
        phases    = @()
        decisions = @()
        retries   = @()
        pause     = [ordered]@{
            active    = $false
            phase     = $null
            reason    = $null
            question  = $null
            options   = @()
            paused_at = $null
        }
        lock = [ordered]@{
            pid         = $null
            acquired_at = $null
        }
        score = [ordered]@{
            total_applicable = 0
            total_passed     = 0
            verdict          = $null
            requirements     = @()
        }
    }

    $jsonOut = $state | ConvertTo-Json -Depth 10 -Compress
    $jsonOut | Set-Content -Path $filePath -NoNewline
    Write-Output $jsonOut
}

function Invoke-Read {
    param([string]$FDir)

    $filePath = Get-StatePath $FDir
    if (-not (Test-Path $filePath)) {
        Write-ErrorJson "Pipeline state file not found: $filePath"
    }

    $content = Get-Content -Path $filePath -Raw
    Write-Output $content
}

function Invoke-Update {
    param([string]$FDir)

    $filePath = Get-StatePath $FDir
    if (-not (Test-Path $filePath)) {
        Write-ErrorJson "Pipeline state file not found: $filePath"
    }

    $state = Get-Content -Path $filePath -Raw | ConvertFrom-Json

    # Update pipeline-level status
    if ($Status) {
        $state.status = $Status
        if ($Status -eq 'completed' -or $Status -eq 'failed') {
            $state.completed_at = Get-Iso8601Now
        }
    }

    # Update phase entry
    if ($Phase -ge 0) {
        # Ensure phases array is large enough
        if ($null -eq $state.phases) {
            $state.phases = @()
        }

        while ($state.phases.Count -le $Phase) {
            $newPhase = [ordered]@{
                phase        = $state.phases.Count
                status       = 'pending'
                gate_result  = $null
                artifacts    = @()
                started_at   = $null
                completed_at = $null
            }
            $state.phases += [PSCustomObject]$newPhase
        }

        if ($PhaseStatus) {
            $state.phases[$Phase].status = $PhaseStatus
            if ($PhaseStatus -eq 'running') {
                $state.phases[$Phase].started_at = Get-Iso8601Now
            } elseif ($PhaseStatus -eq 'completed' -or $PhaseStatus -eq 'failed') {
                $state.phases[$Phase].completed_at = Get-Iso8601Now
            }
        }

        if ($GateResult) {
            $state.phases[$Phase].gate_result = $GateResult
        }

        if ($AddArtifact) {
            if ($null -eq $state.phases[$Phase].artifacts) {
                $state.phases[$Phase].artifacts = @()
            }
            $state.phases[$Phase].artifacts += $AddArtifact
        }
    }

    $jsonOut = $state | ConvertTo-Json -Depth 10 -Compress
    $jsonOut | Set-Content -Path $filePath -NoNewline
    Write-Output $jsonOut
}

function Invoke-Lock {
    param([string]$FDir)

    $filePath = Get-StatePath $FDir
    if (-not (Test-Path $filePath)) {
        Write-ErrorJson "Pipeline state file not found: $filePath"
    }

    $state = Get-Content -Path $filePath -Raw | ConvertFrom-Json

    # Check existing lock
    $existingPid = $state.lock.pid
    if ($null -ne $existingPid) {
        try {
            $proc = Get-Process -Id $existingPid -ErrorAction Stop
            if ($proc) {
                Write-ErrorJson "Lock held by active process $existingPid"
            }
        } catch {
            # PID is dead, reclaim
        }
    }

    $state.lock.pid = $PID
    $state.lock.acquired_at = Get-Iso8601Now

    $jsonOut = $state | ConvertTo-Json -Depth 10 -Compress
    $jsonOut | Set-Content -Path $filePath -NoNewline
    Write-Output $jsonOut
}

function Invoke-Unlock {
    param([string]$FDir)

    $filePath = Get-StatePath $FDir
    if (-not (Test-Path $filePath)) {
        Write-ErrorJson "Pipeline state file not found: $filePath"
    }

    $state = Get-Content -Path $filePath -Raw | ConvertFrom-Json
    $state.lock.pid = $null
    $state.lock.acquired_at = $null

    $jsonOut = $state | ConvertTo-Json -Depth 10 -Compress
    $jsonOut | Set-Content -Path $filePath -NoNewline
    Write-Output $jsonOut
}

# --- Main ---

$resolvedDir = Resolve-FeatureDir $FeatureDir

if ($Subcommand -ne 'init' -and -not (Test-Path $resolvedDir)) {
    Write-ErrorJson "Feature directory not found: $resolvedDir"
}

if ($Subcommand -eq 'init' -and -not (Test-Path $resolvedDir)) {
    New-Item -ItemType Directory -Path $resolvedDir -Force | Out-Null
}

switch ($Subcommand) {
    'init'   { Invoke-Init   $resolvedDir }
    'read'   { Invoke-Read   $resolvedDir }
    'update' { Invoke-Update $resolvedDir }
    'lock'   { Invoke-Lock   $resolvedDir }
    'unlock' { Invoke-Unlock $resolvedDir }
}

exit 0
