# spequa-sync.ps1 — Pre-command hook: check and pull submodule updates
param(
    [switch]$Force,
    [switch]$Quiet,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir/spequa-common.ps1"

$SubmodulePath = ".spequa"
$ConfigFile = ".spequa.json"

if ($Help) {
    Write-Host @"
Usage: spequa-sync.ps1 [-Force] [-Quiet]

Pre-command hook: checks for toolkit updates and pulls if available.

Parameters:
  -Force    Sync even if pinned
  -Quiet    Suppress informational output
"@
    exit 0
}

if (-not (Test-Path $SubmodulePath)) {
    Write-EquaspecError ".spequa/ submodule not found. Run spequa-bootstrap.ps1 first."
    exit 1
}

$config = Read-EquaspecJson -FilePath $ConfigFile

if ($config.pinned -and -not $Force) {
    if (-not $Quiet) { Write-EquaspecInfo "Toolkit is pinned. Skipping sync. Use -Force to override." }
    exit 0
}

if (-not $Quiet) { Write-EquaspecInfo "Checking for toolkit updates..." }

$result = git submodule update --remote --merge $SubmodulePath 2>&1
if ($LASTEXITCODE -eq 0) {
    & "$ScriptDir/spequa-link.ps1"
    $version = git -C $SubmodulePath rev-parse --short HEAD 2>$null
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Write-EquaspecJson -FilePath $ConfigFile -Pinned $config.pinned -LastSync $timestamp -ToolkitVersion $version
    if (-not $Quiet) { Write-EquaspecInfo "Synced to $version." }
} else {
    Write-EquaspecWarn "Could not reach upstream. Using cached toolkit version."
    & "$ScriptDir/spequa-link.ps1" 2>$null
}
