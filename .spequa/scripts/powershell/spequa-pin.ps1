# spequa-pin.ps1 — Pin/unpin toolkit version
param(
    [Parameter(Position=0)]
    [ValidateSet("pin", "unpin", "status")]
    [string]$Command,
    [string]$Version,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir/spequa-common.ps1"

$SubmodulePath = ".spequa"
$ConfigFile = ".spequa.json"

if ($Help -or -not $Command) {
    Write-Host @"
Usage: spequa-pin.ps1 <pin|unpin|status> [-Version SHA]

Manage toolkit version pinning.

Commands:
  pin [-Version SHA]   Pin to current or specified commit
  unpin                Unpin and trigger sync
  status               Show current pin state and version
"@
    exit 0
}

if (-not (Test-Path $ConfigFile)) {
    Write-EquaspecError ".spequa.json not found. Run spequa-bootstrap.ps1 first."
    exit 1
}

$config = Read-EquaspecJson -FilePath $ConfigFile

switch ($Command) {
    "pin" {
        if ($Version) {
            $check = git -C $SubmodulePath cat-file -t $Version 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-EquaspecError "Invalid SHA: $Version"
                exit 2
            }
            Write-EquaspecInfo "Checking out $Version in submodule..."
            git -C $SubmodulePath checkout $Version 2>$null
        }
        $ver = git -C $SubmodulePath rev-parse --short HEAD 2>$null
        Write-EquaspecJson -FilePath $ConfigFile -Pinned $true -LastSync $config.last_sync -ToolkitVersion $ver
        Write-EquaspecInfo "Pinned to $ver. Auto-sync disabled."
    }
    "unpin" {
        $ver = git -C $SubmodulePath rev-parse --short HEAD 2>$null
        Write-EquaspecJson -FilePath $ConfigFile -Pinned $false -LastSync $config.last_sync -ToolkitVersion $ver
        Write-EquaspecInfo "Unpinned. Auto-sync re-enabled."
        Write-EquaspecInfo "Syncing..."
        & "$ScriptDir/spequa-sync.ps1"
    }
    "status" {
        $currentRef = git -C $SubmodulePath rev-parse --short HEAD 2>$null
        Write-Host "Toolkit Status:"
        Write-Host "  Pinned:     $($config.pinned)"
        Write-Host "  Version:    $($config.toolkit_version)"
        Write-Host "  Current:    $currentRef"
        Write-Host "  Last sync:  $(if ($config.last_sync) { $config.last_sync } else { 'never' })"
    }
}
