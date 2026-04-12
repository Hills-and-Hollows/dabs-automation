#!/usr/bin/env pwsh
# lint-config-refs.ps1 — Validate <!-- config-refs: ... --> comments in command templates
# Ensures every referenced config key exists in the schema.
# Exit: 0 if all valid, 1 if any invalid keys found.

$RepoRoot = try { git rev-parse --show-toplevel 2>$null } catch { Get-Location }
$Schema = Join-Path $RepoRoot 'specs/006-layered-command-composition/contracts/config-schema.json'
$TemplatesDir = Join-Path $RepoRoot 'templates/commands'

if (-not (Test-Path $Schema)) {
    Write-Error "Schema not found at $Schema"
    exit 1
}

# Extract valid keys from JSON schema properties
$schemaContent = Get-Content $Schema -Raw
$validKeys = [regex]::Matches($schemaContent, '"([a-z_]+)":') |
    ForEach-Object { $_.Groups[1].Value } |
    Sort-Object -Unique

$errors = 0

Get-ChildItem -Path $TemplatesDir -Filter '*.md' | ForEach-Object {
    $filename = $_.Name
    $content = Get-Content $_.FullName -Raw

    if ($content -match '<!--\s*config-refs:\s*(.+?)\s*-->') {
        $refs = $matches[1] -split ',' | ForEach-Object { $_.Trim() }
        foreach ($key in $refs) {
            if ($key -notin $validKeys) {
                Write-Error "$filename references unknown config key '$key'"
                $script:errors++
            }
        }
    }
}

if ($errors -gt 0) {
    Write-Error "$errors invalid config-ref(s) found"
    exit 1
}

Write-Output 'All config-refs valid'
