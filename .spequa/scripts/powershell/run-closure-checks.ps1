#!/usr/bin/env pwsh

# Structural closure checks for /spequa.16-close (PowerShell parity)
#
# Runs 5 deterministic checks against a spec directory and outputs
# structured JSON for the closure workflow to interpret.
#
# Usage: ./run-closure-checks.ps1 <FEATURE_DIR>
#
# Exit code: Always 0 (caller interprets JSON results)

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$FeatureDir
)

# Normalize to absolute path
if (-not [System.IO.Path]::IsPathRooted($FeatureDir)) {
    $FeatureDir = (Resolve-Path $FeatureDir).Path
}

# --- Check 1: Required artifacts exist ---
$missingFiles = @()
foreach ($required in @('spec.md', 'plan.md', 'tasks.md')) {
    if (-not (Test-Path (Join-Path $FeatureDir $required))) {
        $missingFiles += $required
    }
}

if ($missingFiles.Count -gt 0) {
    $missingJson = ($missingFiles | ForEach-Object { "`"$_`"" }) -join ','
    $detail = "Missing: $($missingFiles -join ', ')"
    Write-Output "{`"overall`":`"BLOCKED`",`"checks`":[{`"name`":`"required_artifacts`",`"result`":`"BLOCK`",`"detail`":`"$detail`"}],`"missing_files`":[$missingJson],`"tasks`":{`"total`":0,`"completed`":0,`"incomplete`":0},`"status_field`":`"`",`"markers`":[],`"sc_items`":[],`"fr_items`":[]}"
    exit 0
}

# --- Check 2: Task completion ---
$totalTasks = 0
$completedTasks = 0
$incompleteTasks = 0
$incompleteList = @()

$tasksContent = Get-Content (Join-Path $FeatureDir 'tasks.md') -Raw
foreach ($line in ($tasksContent -split "`n")) {
    if ($line -match '^\s*-\s*\[[xX]\]') {
        $totalTasks++
        $completedTasks++
    } elseif ($line -match '^\s*-\s*\[\s\]') {
        $totalTasks++
        $incompleteTasks++
        $taskText = ($line -replace '^\s*-\s*\[\s\]\s*', '').Substring(0, [Math]::Min(80, ($line -replace '^\s*-\s*\[\s\]\s*', '').Length))
        $incompleteList += $taskText
    }
}

if ($incompleteTasks -gt 0) {
    $taskResult = 'FAIL'
    $taskDetail = "$incompleteTasks of $totalTasks tasks incomplete"
} else {
    $taskResult = 'PASS'
    $taskDetail = "All $totalTasks tasks complete"
}

# --- Check 3: Spec status field ---
$statusField = ''
$specContent = Get-Content (Join-Path $FeatureDir 'spec.md')
foreach ($line in $specContent) {
    if ($line -match '^\*\*Status\*\*:\s*(.+)') {
        $statusField = $Matches[1].Trim()
        break
    }
}

$statusResult = 'PASS'
$statusDetail = "Current status: $(if ($statusField) { $statusField } else { 'unknown' })"

# --- Check 4: [NEEDS CLARIFICATION] markers ---
$markers = @()
$mdFiles = Get-ChildItem -Path $FeatureDir -Filter '*.md' -Recurse -File

foreach ($mdFile in $mdFiles) {
    $inCodeBlock = $false
    $lineNum = 0
    foreach ($line in (Get-Content $mdFile.FullName)) {
        $lineNum++
        if ($line -match '^```') {
            $inCodeBlock = -not $inCodeBlock
            continue
        }
        if ($inCodeBlock) { continue }

        # Strip inline backtick-quoted references
        $stripped = $line -replace '`[^`]*`', ''
        # Skip checklist items about the marker
        if ($stripped -match '\[NEEDS CLARIFICATION\]' -and
            $stripped -notmatch 'No\s+\[NEEDS CLARIFICATION\]' -and
            $stripped -notmatch 'markers\s+remain') {
            $relPath = $mdFile.FullName.Replace($FeatureDir + [IO.Path]::DirectorySeparatorChar, '')
            $markers += "${relPath}:L${lineNum}"
        }
    }
}

if ($markers.Count -gt 0) {
    $markerResult = 'FAIL'
    $markerDetail = "$($markers.Count) unresolved marker(s) found"
} else {
    $markerResult = 'PASS'
    $markerDetail = 'No unresolved markers'
}

# --- Check 5: Extract SC-* items from spec.md ---
$scItems = @()
foreach ($line in $specContent) {
    if ($line -match '\*\*SC-(\d+)\*\*:\s*(.+)') {
        $scItems += "SC-$($Matches[1]): $($Matches[2])"
    }
}

if ($scItems.Count -eq 0) {
    $scResult = 'FAIL'
    $scDetail = 'No success criteria (SC-*) found in spec.md; spec is malformed'
} else {
    $scResult = 'PASS'
    $scDetail = "$($scItems.Count) success criteria found"
}

# --- Extract FR-* items from spec.md ---
$frItems = @()
foreach ($line in $specContent) {
    if ($line -match '\*\*FR-(\d+)\*\*:\s*(.+)') {
        $frItems += "FR-$($Matches[1]): $($Matches[2])"
    }
}

# --- Compute overall result ---
$overall = 'PASS'
if ($taskResult -eq 'FAIL' -or $markerResult -eq 'FAIL' -or $scResult -eq 'FAIL') {
    $overall = 'FAIL'
}

# --- Build JSON output ---
function ConvertTo-JsonArray {
    param([string[]]$Items)
    if ($Items.Count -eq 0) { return '[]' }
    $escaped = $Items | ForEach-Object { $_ -replace '\\', '\\\\' -replace '"', '\"' }
    $quoted = $escaped | ForEach-Object { "`"$_`"" }
    return "[$($quoted -join ',')]"
}

$checksJson = "[{`"name`":`"required_artifacts`",`"result`":`"PASS`",`"detail`":`"All required files present`"},{`"name`":`"task_completion`",`"result`":`"$taskResult`",`"detail`":`"$taskDetail`"},{`"name`":`"spec_status`",`"result`":`"$statusResult`",`"detail`":`"$statusDetail`"},{`"name`":`"unresolved_markers`",`"result`":`"$markerResult`",`"detail`":`"$markerDetail`"},{`"name`":`"success_criteria`",`"result`":`"$scResult`",`"detail`":`"$scDetail`"}]"

$markersJson = ConvertTo-JsonArray $markers
$scJson = ConvertTo-JsonArray $scItems
$frJson = ConvertTo-JsonArray $frItems
$incompleteJson = ConvertTo-JsonArray $incompleteList

Write-Output "{`"overall`":`"$overall`",`"checks`":$checksJson,`"tasks`":{`"total`":$totalTasks,`"completed`":$completedTasks,`"incomplete`":$incompleteTasks,`"incomplete_list`":$incompleteJson},`"status_field`":`"$statusField`",`"markers`":$markersJson,`"sc_items`":$scJson,`"fr_items`":$frJson}"
exit 0
