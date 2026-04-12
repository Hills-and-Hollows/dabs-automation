# spequa-bootstrap.ps1 — Add spequa as a submodule and create symlinks
param(
    [string]$Remote = "https://github.com/EQUAStart/spequa.git",
    [string]$Branch = "main",
    [string]$Path = ".spequa",
    [string]$Agents = "",  # Comma-separated agent keys (e.g. "claude,cursor-agent,agy")
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir/spequa-common.ps1"

if ($Help) {
    Write-Host @"
Usage: spequa-bootstrap.ps1 [-Remote URL] [-Branch BRANCH] [-Path PATH] [-Force]

Add spequa as a git submodule and create symlinks for SDD toolkit.

Parameters:
  -Remote URL      Remote URL (default: https://github.com/EQUAStart/spequa.git)
  -Branch BRANCH   Tracking branch (default: main)
  -Path PATH       Submodule mount path (default: .spequa)
  -Force           Re-bootstrap even if submodule exists
"@
    exit 0
}

# Preconditions
$gitDir = git rev-parse --git-dir 2>$null
if (-not $gitDir) {
    Write-EquaspecError "Not a git repository. Run 'git init' first."
    exit 1
}

if ((Test-Path $Path) -and -not $Force) {
    Write-EquaspecError "Submodule already exists at '$Path'. Use -Force to re-bootstrap."
    exit 2
}

if ((Test-Path $Path) -and $Force) {
    Write-EquaspecInfo "Removing existing submodule at '$Path'..."
    git submodule deinit -f $Path 2>$null
    git rm -f $Path 2>$null
    Remove-Item -Recurse -Force ".git/modules/$Path" -ErrorAction SilentlyContinue
}

Write-EquaspecInfo "Adding submodule from $Remote at $Path (branch: $Branch)..."
$result = git submodule add -b $Branch $Remote $Path 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-EquaspecError "Failed to add submodule. Is the remote accessible?"
    exit 3
}

git submodule update --init $Path

# Build agents list
$agentsList = @()
if ($Agents -ne "") {
    $agentsList = $Agents.Split(",") | ForEach-Object { $_.Trim() } | Where-Object {
        if ($script:EquaspecAgentKeys.ContainsKey($_)) { $true }
        else { Write-EquaspecWarn "Unknown agent key: $_ (skipping)"; $false }
    }
    Write-EquaspecInfo "Agents (from -Agents): [$($agentsList -join ', ')]"
} else {
    # Auto-detect: check which agent dirs exist locally
    foreach ($key in $script:EquaspecAgentKeys.Keys) {
        $folder = $script:EquaspecAgentKeys[$key]
        if (Test-Path $folder) { $agentsList += $key }
    }
    # Always include claude
    if ($agentsList -notcontains "claude") { $agentsList += "claude" }
    $agentsList = $agentsList | Sort-Object
    Write-EquaspecInfo "Agents (auto-detected): [$($agentsList -join ', ')]"
}

Write-EquaspecInfo "Initializing .spequa.json..."
Write-EquaspecJson -FilePath ".spequa.json" -Pinned $false -Agents $agentsList

Write-EquaspecInfo "Creating symlinks..."
& "$ScriptDir/spequa-link.ps1" -Verbose

Write-EquaspecInfo "Bootstrap complete."
