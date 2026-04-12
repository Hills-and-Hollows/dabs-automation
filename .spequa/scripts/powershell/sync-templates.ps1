#Requires -Version 7.0
<#
.SYNOPSIS
    Propagate templates/commands/ to all agent directories.

.DESCRIPTION
    Reads numbered master templates (e.g. 5-plan.md) and generates:
      1. Numbered agent commands  (spequa.5-plan.md)
      2. Unnumbered alias commands (spequa.plan.md) with cross-refs stripped

    Handles markdown and TOML formats per agent.

.PARAMETER DryRun
    Show what would be written without making changes.

.PARAMETER Verbose
    Print each file written/skipped.

.PARAMETER Force
    Overwrite even if target is newer than template.
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $PSCommandPath
$RepoRoot = (Resolve-Path "$ScriptDir/../..").Path

. "$ScriptDir/common.ps1"

$TemplatesDir = Join-Path $RepoRoot "templates/commands"
if (-not (Test-Path $TemplatesDir)) {
    Write-Error "templates/commands/ not found at $RepoRoot"
    exit 1
}

# Agent directory map: folder, subdir, format, arg_placeholder
$AgentMap = @(
    @{ Folder=".claude";    Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".cursor";    Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".augment";   Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".bob";       Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".comet";     Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".codebuddy"; Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".qoder";     Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".roo";       Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".shai";      Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".agents";    Subdir="commands";   Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".agent";     Subdir="workflows";  Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".codex";     Subdir="prompts";    Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".kiro";      Subdir="prompts";    Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".opencode";  Subdir="command";    Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".windsurf";  Subdir="workflows";  Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".kilocode";  Subdir="workflows";  Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".github";    Subdir="agents";     Format="md";   Args='$ARGUMENTS' }
    @{ Folder=".gemini";    Subdir="commands";   Format="toml"; Args='{{args}}' }
    @{ Folder=".qwen";      Subdir="commands";   Format="toml"; Args='{{args}}' }
)

$Written = 0
$Skipped = 0
$Errors = 0

function Extract-Description {
    param([string]$FilePath)
    $content = Get-Content $FilePath -Raw
    if ($content -match '(?s)^---\n(.*?)\n---') {
        $fm = $Matches[1]
        if ($fm -match 'description:\s*[\"''](.+?)[\"'']') {
            return $Matches[1]
        }
        if ($fm -match 'description:\s*(.+)') {
            return $Matches[1].Trim()
        }
    }
    return ""
}

function Extract-Body {
    param([string]$FilePath)
    $content = Get-Content $FilePath -Raw
    if ($content -match '(?s)^---\n.*?\n---\n?(.*)$') {
        return $Matches[1]
    }
    return $content
}

function Strip-NumberRefs {
    param([string]$Text)
    # /spequa.5-plan → /spequa.plan
    $Text = [regex]::Replace($Text, '(/spequa\.)(\d+(\.\d+)?)-', '$1')
    $Text = [regex]::Replace($Text, '(spequa\.)(\d+(\.\d+)?)-', '$1')
    return $Text
}

function Render-Toml {
    param([string]$Description, [string]$Body)
    $escaped = $Description -replace '"', '\"'
    return "description = `"$escaped`"`n`nprompt = `"`"`"`n$Body`n`"`"`""
}

function Write-AgentFile {
    param([string]$DestPath, [string]$Content)
    if ($DryRun) {
        if ($VerbosePreference -eq 'Continue') {
            Write-Host "[spequa] WOULD WRITE: $DestPath"
        }
        $script:Written++
        return
    }
    $dir = Split-Path -Parent $DestPath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($DestPath, $Content)
    if ($VerbosePreference -eq 'Continue') {
        Write-Host "[spequa] WRITE: $DestPath"
    }
    $script:Written++
}

# Main loop
foreach ($template in Get-ChildItem "$TemplatesDir/*.md") {
    $tplName = $template.Name

    if ($tplName -match '^(\d+(\.\d+)?)-(.+)\.md$') {
        $order = $Matches[1]
        $stem = $Matches[3]
    } else {
        Write-Warning "Skipping non-numbered template: $tplName"
        $Skipped++
        continue
    }

    $description = Extract-Description $template.FullName
    $body = Extract-Body $template.FullName

    if ([string]::IsNullOrWhiteSpace($body)) {
        Write-Warning "Empty body in $tplName - skipping"
        $Errors++
        continue
    }

    foreach ($agent in $AgentMap) {
        $agentDir = Join-Path $RepoRoot "$($agent.Folder)/$($agent.Subdir)"
        if (-not (Test-Path $agentDir)) { continue }

        $agentBody = $body
        if ($agent.Args -ne '$ARGUMENTS') {
            $agentBody = $agentBody -replace [regex]::Escape('$ARGUMENTS'), $agent.Args
        }

        # Numbered variant
        if ($agent.Format -eq "toml") {
            $numberedName = "spequa.$order-$stem.toml"
            $numberedContent = Render-Toml $description $agentBody
        } else {
            $numberedName = "spequa.$order-$stem.md"
            $numberedContent = "---`ndescription: $description`n---`n$agentBody"
        }
        Write-AgentFile (Join-Path $agentDir $numberedName) $numberedContent

        # Clean up legacy unnumbered alias if present
        $legacyExt = if ($agent.Format -eq "toml") { ".toml" } else { ".md" }
        $legacyPath = Join-Path $agentDir "spequa.$stem$legacyExt"
        if (Test-Path $legacyPath) {
            if (-not $DryRun) { Remove-Item $legacyPath }
            if ($VerbosePreference -eq 'Continue') {
                Write-Host "[spequa] DELETE: $legacyPath (unnumbered alias)"
            }
        }
    }
}

$mode = if ($DryRun) { "dry-run" } else { "sync" }
Write-Host "[spequa] Template $mode complete: $Written written, $Skipped skipped, $Errors errors"
