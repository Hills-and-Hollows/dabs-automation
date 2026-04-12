#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # Fall back to script location for non-git repos
    return (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-CurrentBranch {
    # First check if SPEQUAFY_FEATURE environment variable is set
    if ($env:SPEQUAFY_FEATURE) {
        return $env:SPEQUAFY_FEATURE
    }
    
    # Then check git if available
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # For non-git repos, try to find the latest feature directory
    $repoRoot = Get-RepoRoot
    $configSpecDir = ''
    $cfgFile = Join-Path $repoRoot '.spequa/config.yml'
    if (Test-Path $cfgFile) {
        $cfgContent = Get-Content $cfgFile -ErrorAction SilentlyContinue
        foreach ($l in $cfgContent) {
            if ($l -match '^spec_dir:\s*(.+)$') {
                $configSpecDir = $matches[1].Trim() -replace "^[`"']", '' -replace "[`"']$", ''
                break
            }
        }
    }
    if (-not $configSpecDir) { $configSpecDir = 'specs' }
    $specsDir = Join-Path $repoRoot $configSpecDir
    
    if (Test-Path $specsDir) {
        $latestFeature = ""
        $highest = 0
        
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    $latestFeature = $_.Name
                }
            }
        }
        
        if ($latestFeature) {
            return $latestFeature
        }
    }
    
    # Final fallback
    return "main"
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[spequafy] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    
    $bp = Get-EquaspecConfig 'branch_prefix' ''
    $pattern = "^${bp}[0-9]{3}-"
    if ($Branch -notmatch $pattern) {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        if ($bp) {
            Write-Output "Feature branches should be named like: ${bp}001-feature-name"
        } else {
            Write-Output "Feature branches should be named like: 001-feature-name"
        }
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    $sd = Get-EquaspecConfig 'spec_dir' 'specs'
    Join-Path $RepoRoot "$sd/$Branch"
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    
    [PSCustomObject]@{
        REPO_ROOT     = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT       = $hasGit
        FEATURE_DIR   = $featureDir
        FEATURE_SPEC  = Join-Path $featureDir 'spec.md'
        IMPL_PLAN     = Join-Path $featureDir 'plan.md'
        TASKS         = Join-Path $featureDir 'tasks.md'
        RESEARCH      = Join-Path $featureDir 'research.md'
        DATA_MODEL    = Join-Path $featureDir 'data-model.md'
        QUICKSTART    = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR = Join-Path $featureDir 'contracts'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

# ── Config System (spec 006) ──────────────────────────────────────────────

$script:EquaspecConfigKeys = @(
    'primary', 'test_command', 'package_manager', 'branch_prefix',
    'project_root', 'spec_dir', 'custom_scripts', 'custom'
)

function Get-EquaspecConfig {
    param(
        [Parameter(Mandatory)][string]$Key,
        [string]$Default = ''
    )
    $repoRoot = Get-RepoRoot
    $configFile = Join-Path $repoRoot '.spequa/config.yml'

    if (-not (Test-Path $configFile)) {
        return $Default
    }

    $content = Get-Content $configFile -ErrorAction SilentlyContinue
    foreach ($line in $content) {
        if ($line -match "^${Key}:\s*(.+)$") {
            $value = $matches[1].Trim()
            $value = $value -replace "^[`"']", '' -replace "[`"']$", ''
            return $value
        }
    }
    return $Default
}

function Get-EquaspecLevenshtein {
    param([string]$Source, [string]$Target)
    $sLen = $Source.Length
    $tLen = $Target.Length
    if ($Source -eq $Target) { return 0 }
    if ($sLen -eq 0) { return $tLen }
    if ($tLen -eq 0) { return $sLen }

    $row = @(0..$tLen)
    for ($i = 1; $i -le $sLen; $i++) {
        $prev = $i - 1
        $row[0] = $i
        for ($j = 1; $j -le $tLen; $j++) {
            $cost = if ($Source[$i-1] -eq $Target[$j-1]) { 0 } else { 1 }
            $del = $row[$j] + 1
            $ins = $row[$j-1] + 1
            $sub = $prev + $cost
            $prev = $row[$j]
            $row[$j] = [Math]::Min([Math]::Min($del, $ins), $sub)
        }
    }
    return $row[$tLen]
}

function Test-EquaspecConfig {
    $repoRoot = Get-RepoRoot
    $configFile = Join-Path $repoRoot '.spequa/config.yml'

    if (-not (Test-Path $configFile)) {
        return $true
    }

    $valid = $true
    $content = Get-Content $configFile -ErrorAction SilentlyContinue

    foreach ($line in $content) {
        if ($line -match '^([a-zA-Z_][a-zA-Z0-9_]*):') {
            $key = $matches[1]
            if ($key -notin $script:EquaspecConfigKeys) {
                $bestKey = ''
                $bestDist = 3
                foreach ($known in $script:EquaspecConfigKeys) {
                    $dist = Get-EquaspecLevenshtein $key $known
                    if ($dist -lt $bestDist) {
                        $bestDist = $dist
                        $bestKey = $known
                    }
                }
                if ($bestKey) {
                    Write-Warning "[config] Unknown key '$key' in .spequa/config.yml — did you mean '$bestKey'?"
                } else {
                    Write-Warning "[config] Unknown key '$key' in .spequa/config.yml"
                }
                $valid = $false
            }
        }
    }

    # Validate path-valued keys
    $projectRoot = Get-EquaspecConfig 'project_root' '.'
    if ($projectRoot -ne '.' -and -not (Test-Path (Join-Path $repoRoot $projectRoot))) {
        Write-Warning "[config] project_root '$projectRoot' does not exist (expected at $(Join-Path $repoRoot $projectRoot))"
        $valid = $false
    }

    return $valid
}

