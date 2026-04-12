# score-docs-ci.ps1 — Heuristic documentation quality checks for CI pipelines
# Usage: score-docs-ci.ps1 <file1.md> [file2.md] ...
# Exit: 0 = PASS (all files pass), 1 = FAIL (one or more files fail)
# Note: Full 5-dimension semantic scoring is agent-only (FR-012).
#       This script performs structural/heuristic checks only.

param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Files
)

if (-not $Files -or $Files.Count -eq 0) {
    Write-Output "Usage: score-docs-ci.ps1 <file1.md> [file2.md] ..."
    Write-Output "No files provided — nothing to check."
    exit 0
}

$OverallPass = $true
$Report = @()

foreach ($Doc in $Files) {
    if (-not (Test-Path $Doc)) {
        $Report += "## $Doc`n- SKIP: File does not exist`n"
        continue
    }

    $FilePass = $true
    $FileFindings = @()
    $Content = Get-Content $Doc -Raw
    $DocDir = Split-Path $Doc -Parent
    if (-not $DocDir) { $DocDir = "." }

    # Check 1: Dead internal markdown links
    $links = [regex]::Matches($Content, '\[([^\]]*)\]\(([^)]+)\)') | ForEach-Object { $_.Groups[2].Value }
    $localLinks = $links | Where-Object { $_ -notmatch '^http' -and $_ -notmatch '^mailto' -and $_ -notmatch '^\#' }
    foreach ($link in $localLinks) {
        $targetPath = $link -replace '#.*$', ''
        if ($targetPath) {
            $fullPath = Join-Path $DocDir $targetPath
            if (-not (Test-Path $fullPath)) {
                $FileFindings += "  - Dead link: [$link]"
                $FilePass = $false
            }
        }
    }
    if ($FileFindings.Count -gt 0) {
        $deadLinkFindings = $FileFindings -join "`n"
        $FileFindings = @("- Dead links found:`n$deadLinkFindings")
    }

    # Check 2: Required sections for known doc types
    $BaseName = Split-Path $Doc -Leaf
    switch ($BaseName) {
        "README.md" {
            if ($Content -notmatch '(?m)^##?\s') {
                $FileFindings += "- Missing headings: No heading found"
                $FilePass = $false
            }
        }
        "CHANGELOG.md" {
            if ($Content -notmatch '(?m)^##?\s') {
                $FileFindings += "- Missing version headings in CHANGELOG"
                $FilePass = $false
            }
        }
    }

    # Check 3: Stale references
    $refs = [regex]::Matches($Content, '`(src/[^`]+|scripts/[^`]+|templates/[^`]+|docs/[^`]+)`') | ForEach-Object { $_.Groups[1].Value }
    foreach ($ref in $refs) {
        if (-not (Test-Path $ref)) {
            $FileFindings += "- Stale reference: ``$ref`` does not exist"
            $FilePass = $false
        }
    }

    # Check 4: Unresolved placeholders (exclude backtick-quoted references)
    $strippedContent = $Content -replace '`[^`]*`', ''
    if ($strippedContent -match '\[NEEDS CLARIFICATION\]|\[TODO\]|\[TBD\]|\[PLACEHOLDER\]|TKTK') {
        $FileFindings += "- Unresolved placeholders found"
        $FilePass = $false
    }

    if ($FilePass) {
        $Report += "## $Doc`n- PASS: All heuristic checks passed`n"
    } else {
        $findings = $FileFindings -join "`n"
        $Report += "## $Doc`n- FAIL:`n$findings`n"
        $OverallPass = $false
    }
}

Write-Output "# Documentation Quality Check (CI)"
Write-Output ""
if ($OverallPass) {
    Write-Output "**Result**: PASS"
} else {
    Write-Output "**Result**: FAIL"
}
Write-Output ""
$Report | ForEach-Object { Write-Output $_ }

if ($OverallPass) { exit 0 } else { exit 1 }
