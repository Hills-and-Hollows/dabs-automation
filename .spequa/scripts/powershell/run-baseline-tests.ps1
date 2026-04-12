# run-baseline-tests.ps1 — Run project test suite and output structured Markdown baseline
# Usage: run-baseline-tests.ps1 [-ProjectRoot <path>]
# Output: Markdown per contracts/baseline-tests-format.md on stdout
# Exit: 0 always (caller decides how to handle results)

param(
    [string]$ProjectRoot = "."
)

Set-Location $ProjectRoot

$Branch = try { git rev-parse --abbrev-ref HEAD 2>$null } catch { "unknown" }
$Captured = Get-Date -Format "yyyy-MM-dd HH:mm"
$Timeout = 60

# Read config value from .spequa/config.yml with fallback default (spec 006)
function Read-Config {
    param([string]$Key, [string]$Default)
    $configFile = Join-Path '.' '.spequa/config.yml'
    if (-not (Test-Path $configFile)) { return $Default }
    $content = Get-Content $configFile -ErrorAction SilentlyContinue
    foreach ($line in $content) {
        if ($line -match "^${Key}:\s*(.+)$") {
            $val = $matches[1].Trim()
            $val = $val -replace "^[`"']", '' -replace "[`"']$", ''
            return $val
        }
    }
    return $Default
}

# Resolve test command and runner from config (spec 006)
$TestCommand = Read-Config 'test_command' 'uv run pytest --tb=short -q'
$PkgManager = Read-Config 'package_manager' 'uv'

# Extract runner name for display
$Runner = switch -Wildcard ($TestCommand) {
    '*pytest*'     { 'pytest' }
    '*jest*'       { 'jest' }
    '*vitest*'     { 'vitest' }
    '*cargo test*' { 'cargo-test' }
    '*go test*'    { 'go-test' }
    '*mvn test*'   { 'maven' }
    '*npm test*'   { 'npm-test' }
    default        { 'custom' }
}

# Check if the test tool is available
$TestExec = ($TestCommand -split ' ')[0]
$testPath = Get-Command $TestExec -ErrorAction SilentlyContinue
if (-not $testPath) {
    @"
# Baseline Test Results

**Captured**: $Captured | **Branch**: $Branch | **Runner**: $Runner

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | 0      |
| Passed     | 0      |
| Failed     | 0      |
| Skipped    | 0      |
| Status     | SKIP   |

> Test runner not available ($TestExec not found in PATH).
"@
    exit 0
}

# Run pytest with timeout
try {
    $job = Start-Job -ScriptBlock {
        param($root, $cmd)
        Set-Location $root
        Invoke-Expression "$cmd 2>&1"
    } -ArgumentList (Get-Location).Path, $TestCommand

    $completed = Wait-Job $job -Timeout $Timeout
    if (-not $completed) {
        Stop-Job $job
        Remove-Job $job -Force
        @"
# Baseline Test Results

**Captured**: $Captured | **Branch**: $Branch | **Runner**: $Runner

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | 0      |
| Passed     | 0      |
| Failed     | 0      |
| Skipped    | 0      |
| Status     | SKIP   |

> Test suite exceeded $Timeout-second timeout.
"@
        exit 0
    }

    $Output = Receive-Job $job
    Remove-Job $job
    $OutputText = $Output -join "`n"
}
catch {
    @"
# Baseline Test Results

**Captured**: $Captured | **Branch**: $Branch | **Runner**: $Runner

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | 0      |
| Passed     | 0      |
| Failed     | 0      |
| Skipped    | 0      |
| Status     | SKIP   |

> No tests found or test framework error.
"@
    exit 0
}

# Parse pytest summary line
$SummaryLine = ($OutputText -split "`n") | Where-Object { $_ -match '\d+ passed|\d+ failed|\d+ skipped|\d+ error' } | Select-Object -Last 1

$Passed = 0; $Failed = 0; $Skipped = 0; $Errors = 0

if ($SummaryLine -match '(\d+) passed') { $Passed = [int]$Matches[1] }
if ($SummaryLine -match '(\d+) failed') { $Failed = [int]$Matches[1] }
if ($SummaryLine -match '(\d+) skipped') { $Skipped = [int]$Matches[1] }
if ($SummaryLine -match '(\d+) error') { $Errors = [int]$Matches[1] }

$Total = $Passed + $Failed + $Skipped + $Errors

# Determine status
if ($Total -eq 0) { $Status = "SKIP" }
elseif ($Failed -gt 0 -or $Errors -gt 0) { $Status = "WARN" }
else { $Status = "PASS" }

# Check for coverage
$Coverage = ""
if ($OutputText -match 'TOTAL\s+\d+\s+\d+\s+([\d.]+%)') { $Coverage = $Matches[1] }

# Output baseline Markdown
$result = @"
# Baseline Test Results

**Captured**: $Captured | **Branch**: $Branch | **Runner**: $Runner

## Summary

| Metric     | Value  |
|------------|--------|
| Total      | $Total |
| Passed     | $Passed |
| Failed     | $Failed |
| Skipped    | $Skipped |
"@

if ($Coverage) {
    $result += "`n| Coverage   | $Coverage |"
}

$result += "`n| Status     | $Status |"

# Include failure details if any
if ($Status -eq "WARN") {
    $result += "`n`n## Failures`n"
    $failedLines = ($OutputText -split "`n") | Where-Object { $_ -match '^FAILED |^ERROR ' }
    foreach ($line in $failedLines) {
        $testName = $line -replace '^FAILED |^ERROR ', '' -replace ' - .*$', ''
        $result += "`n### $testName`n`n``````n$line`n```````n"
    }
}

Write-Output $result
