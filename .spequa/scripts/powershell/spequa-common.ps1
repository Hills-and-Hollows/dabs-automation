# spequa-common.ps1 — Shared helper functions for spequa-* scripts
# Dot-source this file, do not execute directly.

function Write-EquaspecInfo  { param([string]$Message) Write-Host "[spequa] $Message" }
function Write-EquaspecWarn  { param([string]$Message) Write-Warning "[spequa] $Message" }
function Write-EquaspecError { param([string]$Message) Write-Error "[spequa] ERROR: $Message" }

function Get-EquaspecRelativePath {
    param([string]$From, [string]$To)
    $fromUri = New-Object System.Uri("$From/")
    $toUri = New-Object System.Uri($To)
    $relPath = $fromUri.MakeRelativeUri($toUri).ToString().Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    return $relPath
}

# Agent folder-to-key mapping
$script:EquaspecAgentFolders = @{
    ".github"    = "copilot"
    ".claude"    = "claude"
    ".gemini"    = "gemini"
    ".cursor"    = "cursor-agent"
    ".qwen"      = "qwen"
    ".opencode"  = "opencode"
    ".codex"     = "codex"
    ".windsurf"  = "windsurf"
    ".kilocode"  = "kilocode"
    ".augment"   = "auggie"
    ".codebuddy" = "codebuddy"
    ".qoder"     = "qodercli"
    ".roo"       = "roo"
    ".kiro"      = "kiro-cli"
    ".agents"    = "amp"
    ".shai"      = "shai"
    ".agent"     = "agy"
    ".bob"       = "bob"
    ".comet"     = "comet"
}

# Reverse lookup: agent key → folder name
$script:EquaspecAgentKeys = @{
    "copilot"      = ".github"
    "claude"       = ".claude"
    "gemini"       = ".gemini"
    "cursor-agent" = ".cursor"
    "qwen"         = ".qwen"
    "opencode"     = ".opencode"
    "codex"        = ".codex"
    "windsurf"     = ".windsurf"
    "kilocode"     = ".kilocode"
    "auggie"       = ".augment"
    "codebuddy"    = ".codebuddy"
    "qodercli"     = ".qoder"
    "roo"          = ".roo"
    "kiro-cli"     = ".kiro"
    "amp"          = ".agents"
    "shai"         = ".shai"
    "agy"          = ".agent"
    "bob"          = ".bob"
    "comet"        = ".comet"
}

function Write-EquaspecJson {
    param(
        [string]$FilePath,
        [bool]$Pinned = $false,
        [string]$LastSync = $null,
        [string]$ToolkitVersion = $null,
        [string[]]$Agents = $null
    )
    $obj = [ordered]@{
        pinned = $Pinned
    }
    if ($Agents -and $Agents.Count -gt 0) {
        $obj["agents"] = $Agents
    } elseif (Test-Path $FilePath) {
        # Preserve existing agents list
        $existing = Read-EquaspecJson -FilePath $FilePath
        if ($existing.agents) {
            $obj["agents"] = @($existing.agents)
        }
    }
    $obj["last_sync"] = $LastSync
    $obj["toolkit_version"] = $ToolkitVersion
    $obj | ConvertTo-Json | Set-Content -Path $FilePath -Encoding UTF8
}

function Read-EquaspecJson {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath)) {
        return @{ pinned = $false; agents = @(); last_sync = $null; toolkit_version = $null }
    }
    return Get-Content -Path $FilePath -Raw | ConvertFrom-Json
}

function Test-EquaspecAgentAllowed {
    param(
        [string]$FolderName,
        [string]$ConfigFile = ".spequa.json"
    )
    if (-not (Test-Path $ConfigFile)) { return $true }
    $config = Read-EquaspecJson -FilePath $ConfigFile
    if (-not $config.agents -or $config.agents.Count -eq 0) { return $true }  # No filter = allow all
    $agentKey = $script:EquaspecAgentFolders[$FolderName]
    if (-not $agentKey) { return $false }
    return $config.agents -contains $agentKey
}
