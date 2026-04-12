#!/usr/bin/env pwsh

# Pipeline scorecard generator (PowerShell parity)
#
# Evaluates a completed pipeline run against 10 binary requirements (R1-R10)
# and generates a scorecard.md in the feature directory.
#
# Usage: ./generate-scorecard.ps1 -FeatureDir <path> [-Json]
#
# Exit code: Always 0 (caller interprets results)

param(
    [Parameter(Mandatory=$true)]
    [string]$FeatureDir,

    [switch]$Json
)

# Normalize to absolute path
if (-not [System.IO.Path]::IsPathRooted($FeatureDir)) {
    $FeatureDir = (Resolve-Path $FeatureDir).Path
}

# --- Load pipeline state ---
$stateFile = Join-Path $FeatureDir '.pipeline-state.json'
$auditFile = Join-Path $FeatureDir 'audit-trail.md'
$specFile  = Join-Path $FeatureDir 'spec.md'
$tasksFile = Join-Path $FeatureDir 'tasks.md'

if (-not (Test-Path $stateFile)) {
    Write-Error ".pipeline-state.json not found in $FeatureDir"
    exit 0
}

$stateContent = Get-Content $stateFile -Raw
$stateObj = $stateContent | ConvertFrom-Json

# Extract spec_id and feature_name from directory name
$dirName = Split-Path $FeatureDir -Leaf
$specId = ($dirName -split '-', 2)[0]
$featureName = ($dirName -split '-', 2)[1]

# Extract run_id
$runId = if ($stateObj.PSObject.Properties['run_id']) { $stateObj.run_id } else { 'unknown' }

# Current timestamp
$completedAt = Get-Date -Format 'o'

# --- Requirement evaluation ---
$requirements = @()

# Helper: add a requirement result
function Add-Requirement {
    param([string]$Name, [string]$Verdict, [string]$Proof, [string]$Diagnostic)
    $script:requirements += [PSCustomObject]@{
        Name       = $Name
        Verdict    = $Verdict
        Proof      = $Proof
        Diagnostic = $Diagnostic
    }
}

# --- R1: Autonomous Execution ---
if (-not (Test-Path $auditFile)) {
    Add-Requirement 'Autonomous Execution' 'FAIL' 'audit-trail.md not found' "R1: audit-trail.md does not exist in $dirName"
} else {
    $auditContent = Get-Content $auditFile -Raw
    $manualCount = ([regex]::Matches($auditContent, 'manual transition', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)).Count
    if ($manualCount -gt 0) {
        Add-Requirement 'Autonomous Execution' 'FAIL' "$manualCount manual transition(s) in audit trail" "R1: Found $manualCount manual transition entries in audit-trail.md. Pipeline should execute autonomously."
    } else {
        Add-Requirement 'Autonomous Execution' 'PASS' 'audit-trail.md present, no manual transitions' ''
    }
}

# --- R2: Spec Completeness ---
if (-not (Test-Path $specFile)) {
    Add-Requirement 'Spec Completeness' 'FAIL' 'spec.md not found' "R2: spec.md does not exist in $dirName"
} else {
    $specLines = Get-Content $specFile
    $inCode = $false
    $markerHits = @()
    $lineNum = 0

    foreach ($line in $specLines) {
        $lineNum++
        if ($line -match '^```') {
            $inCode = -not $inCode
            continue
        }
        if ($inCode) { continue }
        $stripped = $line -replace '`[^`]*`', ''
        if ($stripped -match '\bTODO\b|\bTBD\b|\[placeholder\]|\[NEEDS CLARIFICATION\]') {
            $markerHits += "L$lineNum"
        }
    }

    if ($markerHits.Count -gt 0) {
        Add-Requirement 'Spec Completeness' 'FAIL' "$($markerHits.Count) unresolved marker(s) at $($markerHits -join ', ')" "R2: spec.md contains $($markerHits.Count) TODO/TBD/placeholder markers: $($markerHits -join ', ')"
    } else {
        Add-Requirement 'Spec Completeness' 'PASS' 'spec.md clean, no TODO/TBD/placeholder markers' ''
    }
}

# --- R3: Decision Traceability ---
if ($stateContent -match '"decisions"') {
    $missingEvidence = ([regex]::Matches($stateContent, '"evidence"\s*:\s*""')).Count
    $totalDecisions = ([regex]::Matches($stateContent, '"decision_id"')).Count

    if ($totalDecisions -eq 0) {
        Add-Requirement 'Decision Traceability' 'PASS' 'No decisions recorded in state' ''
    } elseif ($missingEvidence -gt 0) {
        Add-Requirement 'Decision Traceability' 'FAIL' "$missingEvidence of $totalDecisions decision(s) missing evidence" "R3: $missingEvidence decision(s) lack evidence or human resolution in pipeline state"
    } else {
        Add-Requirement 'Decision Traceability' 'PASS' "All $totalDecisions decision(s) have evidence or resolution" ''
    }
} else {
    Add-Requirement 'Decision Traceability' 'PASS' 'No decisions section in state (none required)' ''
}

# --- R4: AC Mapping ---
if (-not (Test-Path $tasksFile)) {
    Add-Requirement 'AC Mapping' 'FAIL' 'tasks.md not found' "R4: tasks.md does not exist in $dirName"
} else {
    $tasksContent = Get-Content $tasksFile -Raw
    $usCount = ([regex]::Matches($tasksContent, '\[US')).Count
    $acCount = ([regex]::Matches($tasksContent, '\[AC')).Count

    if ($usCount -eq 0 -and $acCount -eq 0) {
        Add-Requirement 'AC Mapping' 'FAIL' 'No [US or [AC references found in tasks.md' "R4: tasks.md has no user story or acceptance criteria mappings. Tasks must trace to spec requirements."
    } else {
        Add-Requirement 'AC Mapping' 'PASS' "$usCount [US tag(s), $acCount [AC reference(s)" ''
    }
}

# --- R5: Task Completion ---
if (-not (Test-Path $tasksFile)) {
    Add-Requirement 'Task Completion' 'FAIL' 'tasks.md not found' "R5: tasks.md does not exist in $dirName"
} else {
    $tasksLines = Get-Content $tasksFile
    $totalTasks = 0
    $completedTasks = 0
    $incompleteTasks = 0

    foreach ($line in $tasksLines) {
        if ($line -match '^\s*-\s*\[[xX]\]') {
            $totalTasks++
            $completedTasks++
        } elseif ($line -match '^\s*-\s*\[\s\]') {
            $totalTasks++
            $incompleteTasks++
        }
    }

    $stateTodos = ([regex]::Matches($stateContent, '\bTODO\b|\bFIXME\b', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)).Count

    if ($incompleteTasks -gt 0) {
        Add-Requirement 'Task Completion' 'FAIL' "$incompleteTasks of $totalTasks task(s) incomplete" "R5: $incompleteTasks task(s) remain unchecked in tasks.md"
    } elseif ($stateTodos -gt 0) {
        Add-Requirement 'Task Completion' 'FAIL' "$stateTodos TODO/FIXME marker(s) in pipeline state" "R5: Pipeline state contains $stateTodos TODO/FIXME markers"
    } else {
        Add-Requirement 'Task Completion' 'PASS' "$completedTasks/$totalTasks tasks complete, no TODO/FIXME in state" ''
    }
}

# --- Extract phase status/gate helpers (used by R6, R7, R8) ---
function Get-PhaseField {
    param([string]$PhaseName, [string]$FieldName, [string]$Content)
    if ($Content -match "`"name`"\s*:\s*`"$PhaseName`"") {
        # Extract the field from the same phase object block
        if ($Content -match "`"name`"\s*:\s*`"$PhaseName`"[^]]*?`"$FieldName`"\s*:\s*`"([^`"]*)`"") {
            return $Matches[1]
        }
    }
    return ''
}

$hasPhase7 = $stateContent -match '"name"\s*:\s*"review"'
$phase7Status = Get-PhaseField 'review' 'status' $stateContent
$phase7Gate = Get-PhaseField 'review' 'gate_result' $stateContent

# --- R6: CI Gate ---
if ($hasPhase7) {
    if ($phase7Status -eq 'skipped') {
        Add-Requirement 'CI Gate' 'EXCLUDED' 'Phase 7 (review) skipped - no CI configured' ''
    } elseif ($phase7Gate -eq 'PASS') {
        Add-Requirement 'CI Gate' 'PASS' 'Phase 7 gate_result=PASS' ''
    } else {
        $gateDisplay = if ($phase7Gate) { $phase7Gate } else { 'unknown' }
        Add-Requirement 'CI Gate' 'FAIL' "Phase 7 (review) gate=$gateDisplay" "R6: CI gate (phase 7) did not report gate_result=PASS"
    }
} else {
    Add-Requirement 'CI Gate' 'EXCLUDED' 'No phase 7 (review) in pipeline state - no CI configured' ''
}

# --- R7: Review Gate ---
if ($hasPhase7) {
    if ($phase7Status -in @('completed', 'passed') -or $phase7Gate -eq 'PASS') {
        Add-Requirement 'Review Gate' 'PASS' "Phase 7 (review) status=$phase7Status, gate=$phase7Gate" ''
    } elseif ($phase7Status -eq 'skipped') {
        Add-Requirement 'Review Gate' 'FAIL' 'Phase 7 (review) was skipped' "R7: Review phase was skipped - cannot verify 14-gate checklist"
    } else {
        $statusDisplay = if ($phase7Status) { $phase7Status } else { 'missing' }
        Add-Requirement 'Review Gate' 'FAIL' "Phase 7 (review) status=$statusDisplay" "R7: Review phase did not complete successfully. Status: $statusDisplay"
    }
} else {
    Add-Requirement 'Review Gate' 'FAIL' 'No phase 7 (review) found in pipeline state' 'R7: Pipeline state has no review phase entry'
}

# --- R8: Deploy Gate ---
$deployTarget = if ($stateObj.PSObject.Properties['deploy_target']) { $stateObj.deploy_target } else { '' }
if ($deployTarget -eq 'none') {
    Add-Requirement 'Deploy Gate' 'EXCLUDED' 'deploy_target=none in config' ''
} elseif ($stateContent -match '"name"\s*:\s*"deploy"') {
    $phase8Status = Get-PhaseField 'deploy' 'status' $stateContent
    $phase8Gate = Get-PhaseField 'deploy' 'gate_result' $stateContent

    if ($phase8Status -eq 'completed' -or $phase8Gate -eq 'PASS') {
        Add-Requirement 'Deploy Gate' 'PASS' "Phase 8 (deploy) status=$phase8Status" ''
    } else {
        $statusDisplay = if ($phase8Status) { $phase8Status } else { 'missing' }
        Add-Requirement 'Deploy Gate' 'FAIL' "Phase 8 (deploy) status=$statusDisplay" "R8: Deploy phase did not complete successfully. Status: $statusDisplay"
    }
} else {
    Add-Requirement 'Deploy Gate' 'FAIL' 'No phase 8 (deploy) found in pipeline state' 'R8: Pipeline state has no deploy phase entry'
}

# --- R9: Retry Hygiene ---
if ($stateContent -match '"retries"|"retry"') {
    $retryCount = ([regex]::Matches($stateContent, '"retry_id"|"attempt"')).Count
    if ($retryCount -gt 0) {
        $strategyMatches = [regex]::Matches($stateContent, '"strategy"\s*:\s*"([^"]*)"')
        $strategies = $strategyMatches | ForEach-Object { $_.Groups[1].Value }
        $uniqueStrategies = $strategies | Sort-Object -Unique

        if ($strategies.Count -ne $uniqueStrategies.Count) {
            Add-Requirement 'Retry Hygiene' 'FAIL' "$($strategies.Count) retries with only $($uniqueStrategies.Count) unique strategies" "R9: Retries reused the same strategy. Each retry must use a different approach."
        } else {
            Add-Requirement 'Retry Hygiene' 'PASS' "$retryCount retry(ies) with distinct strategies" ''
        }
    } else {
        Add-Requirement 'Retry Hygiene' 'PASS' 'No retries occurred (auto-PASS)' ''
    }
} else {
    Add-Requirement 'Retry Hygiene' 'PASS' 'No retries occurred (auto-PASS)' ''
}

# --- R10: Audit Completeness ---
if (-not (Test-Path $auditFile)) {
    Add-Requirement 'Audit Completeness' 'FAIL' 'audit-trail.md not found' "R10: audit-trail.md does not exist in $dirName"
} else {
    $auditLines = Get-Content $auditFile
    $auditEntries = ($auditLines | Where-Object { $_ -match '^\s*##\s|^\s*\*\*Phase|\|\s*[0-9]' }).Count

    if ($auditEntries -eq 0) {
        Add-Requirement 'Audit Completeness' 'FAIL' 'audit-trail.md has no phase entries' "R10: audit-trail.md exists but contains no recognizable phase entries"
    } else {
        Add-Requirement 'Audit Completeness' 'PASS' "$auditEntries audit entry(ies) found" ''
    }
}

# --- Scoring ---
$passCount = ($requirements | Where-Object { $_.Verdict -eq 'PASS' }).Count
$failCount = ($requirements | Where-Object { $_.Verdict -eq 'FAIL' }).Count
$excludedCount = ($requirements | Where-Object { $_.Verdict -eq 'EXCLUDED' }).Count
$applicable = 10 - $excludedCount

if ($applicable -gt 0) {
    $scorePct = [Math]::Floor($passCount * 100 / $applicable)
} else {
    $scorePct = 100
}

# --- Determine verdict ---
$threshold = 80

if ($failCount -eq 0) {
    $verdict = 'PRODUCTION_READY'
} elseif ($scorePct -ge $threshold) {
    $verdict = 'CONDITIONAL_PASS'
} elseif ($scorePct -ge 50) {
    $verdict = 'NEEDS_REMEDIATION'
} else {
    $verdict = 'CRITICAL_FAILURE'
}

# --- Extract execution summary metrics ---
$totalDuration = if ($stateObj.PSObject.Properties['total_duration']) { $stateObj.total_duration } else { 'N/A' }
$phasesCompleted = ([regex]::Matches($stateContent, '"status"\s*:\s*"(passed|complete)"')).Count
$totalPhases = ([regex]::Matches($stateContent, '"phase_\d"')).Count
if ($totalPhases -eq 0) { $totalPhases = 'N/A' }

# --- Generate scorecard.md ---
$scorecardPath = Join-Path $FeatureDir 'scorecard.md'

$sb = [System.Text.StringBuilder]::new()
[void]$sb.AppendLine("# Pipeline Scorecard: ${specId}-${featureName}")
[void]$sb.AppendLine()
[void]$sb.AppendLine("**Run ID**: ${runId}")
[void]$sb.AppendLine("**Completed**: ${completedAt}")
[void]$sb.AppendLine("**Score**: ${passCount}/${applicable}")
[void]$sb.AppendLine("**Verdict**: ${verdict}")
[void]$sb.AppendLine()
[void]$sb.AppendLine('## Requirements')
[void]$sb.AppendLine()
[void]$sb.AppendLine('| # | Requirement | Verdict | Proof |')
[void]$sb.AppendLine('|---|-------------|---------|-------|')

for ($i = 0; $i -lt $requirements.Count; $i++) {
    $r = $requirements[$i]
    $idx = $i + 1
    [void]$sb.AppendLine("| R${idx} | $($r.Name) | $($r.Verdict) | $($r.Proof) |")
}

[void]$sb.AppendLine()
[void]$sb.AppendLine('## Diagnostics')
[void]$sb.AppendLine()

$hasDiag = $false
foreach ($r in $requirements) {
    if ($r.Diagnostic) {
        [void]$sb.AppendLine("- $($r.Diagnostic)")
        $hasDiag = $true
    }
}
if (-not $hasDiag) {
    [void]$sb.AppendLine('No failures detected.')
}

[void]$sb.AppendLine()
[void]$sb.AppendLine('## Execution Summary')
[void]$sb.AppendLine()
[void]$sb.AppendLine('| Metric | Value |')
[void]$sb.AppendLine('|--------|-------|')
[void]$sb.AppendLine("| Total Duration | ${totalDuration} |")
[void]$sb.AppendLine("| Phases Completed | ${phasesCompleted}/${totalPhases} |")
[void]$sb.AppendLine("| Pass | ${passCount} |")
[void]$sb.AppendLine("| Fail | ${failCount} |")
[void]$sb.AppendLine("| Excluded | ${excludedCount} |")
[void]$sb.AppendLine("| Score | ${scorePct}% |")

$sb.ToString() | Set-Content $scorecardPath -NoNewline

# --- JSON output ---
$reqsJson = @()
for ($i = 0; $i -lt $requirements.Count; $i++) {
    $r = $requirements[$i]
    $idx = $i + 1
    $escapedProof = $r.Proof -replace '\\', '\\\\' -replace '"', '\"'
    $reqsJson += "{`"id`":`"R${idx}`",`"name`":`"$($r.Name)`",`"verdict`":`"$($r.Verdict)`",`"proof`":`"${escapedProof}`"}"
}

$jsonSummary = "{`"score`":`"${passCount}/${applicable}`",`"verdict`":`"${verdict}`",`"scorecard_path`":`"${scorecardPath}`",`"requirements`":[$(($reqsJson -join ','))]}"

if ($Json) {
    Write-Output $jsonSummary
}

exit 0
