# spequa-link.ps1 — Create/refresh symlinks from project dirs to submodule
param(
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir/spequa-common.ps1"

$SubmodulePath = ".spequa"

if ($Help) {
    Write-Host @"
Usage: spequa-link.ps1 [-DryRun] [-Verbose]

Create or refresh symlinks from project directories to .spequa/ submodule.

Parameters:
  -DryRun    Show what would be linked without making changes
  -Verbose   Print each symlink created/skipped
"@
    exit 0
}

if (-not (Test-Path $SubmodulePath)) {
    Write-EquaspecError ".spequa/ submodule not found. Run spequa-bootstrap.ps1 first."
    exit 1
}

$Created = 0; $Skipped = 0; $Orphaned = 0

$ConfigFile = ".spequa.json"

# Discover agent command directories dynamically
Get-ChildItem -Path $SubmodulePath -Directory -Force | Where-Object {
    $_.Name -match '^\.' -and $_.Name -ne '.git' -and $_.Name -ne '.spequa'
} | Where-Object {
    Test-EquaspecAgentAllowed -FolderName $_.Name -ConfigFile $ConfigFile
} | ForEach-Object {
    $agentDir = $_
    # Only process subdirectories that contain spequa.* files
    # Safely skips non-agent dirs like .github/workflows/ and .github/ISSUE_TEMPLATE/
    Get-ChildItem -Path $agentDir.FullName -Directory | Where-Object {
        (Get-ChildItem -Path $_.FullName -Filter "spequa.*" -File -ErrorAction SilentlyContinue).Count -gt 0
    } | ForEach-Object {
        $cmdDir = $_
        Get-ChildItem -Path $cmdDir.FullName -File | ForEach-Object {
            $file = $_
            $localPath = $file.FullName.Replace("$SubmodulePath/", "").Replace("$SubmodulePath\", "")
            $targetPath = Join-Path "." $localPath

            if ((Test-Path $targetPath) -and -not ((Get-Item $targetPath).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
                $Skipped++
                if ($Verbose) { Write-EquaspecInfo "SKIP (override): $targetPath" }
            } else {
                if ($DryRun) {
                    Write-EquaspecInfo "WOULD LINK: $targetPath"
                } else {
                    $targetDir = Split-Path -Parent $targetPath
                    if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
                    if (Test-Path $targetPath) { Remove-Item $targetPath -Force }
                    New-Item -ItemType SymbolicLink -Path $targetPath -Target $file.FullName -Force | Out-Null
                    if ($Verbose) { Write-EquaspecInfo "LINK: $targetPath -> $($file.FullName)" }
                }
                $Created++
            }
        }
    }
}

# NEVER symlink project-local files — they must remain under project control:
#   - .spequa/memory/     (project constitution and memory)
#   - .spequa/config.yml  (project configuration — spec 006)
#   - .spequa/overrides/  (per-section command overrides — spec 006)

# Symlink .spequa/scripts/ and .spequa/templates/
foreach ($dir in @("scripts", "templates")) {
    $source = Join-Path $SubmodulePath ".spequa/$dir"
    $target = ".spequa/$dir"
    if (Test-Path $source) {
        if ((Test-Path $target) -and -not ((Get-Item $target).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            $Skipped++
            if ($Verbose) { Write-EquaspecInfo "SKIP (override dir): $target" }
        } else {
            if ($DryRun) {
                Write-EquaspecInfo "WOULD LINK DIR: $target"
            } else {
                $targetParent = Split-Path -Parent $target
                if (-not (Test-Path $targetParent)) { New-Item -ItemType Directory -Path $targetParent -Force | Out-Null }
                if (Test-Path $target) { Remove-Item $target -Force }
                New-Item -ItemType SymbolicLink -Path $target -Target (Resolve-Path $source).Path -Force | Out-Null
                if ($Verbose) { Write-EquaspecInfo "LINK DIR: $target" }
            }
            $Created++
        }
    }
}

Write-EquaspecInfo "Symlink summary: $Created created, $Skipped overrides skipped, $Orphaned orphaned"
