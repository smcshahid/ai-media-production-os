#Requires -Version 5.1
<#
.SYNOPSIS
  Generate release notes markdown from git history since baseline tag.
#>
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [string]$BaselineTag = "v0.12.0-usv03",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if (-not $OutDir) {
    $OutDir = Join-Path $RepoRoot "docs/release/notes"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$date = Get-Date -Format "yyyy-MM-dd"
$commit = ""
try {
    $commit = (git rev-parse HEAD).Trim()
} catch {
    $commit = "unknown"
}

$log = ""
try {
    $log = git log "$BaselineTag..HEAD" --oneline --no-decorate 2>$null
} catch {
    $log = "(git log unavailable — run from repository root)"
}

$body = @"
# AIMPOS-Spark $Version

**Date:** $date  
**Commit:** $commit  
**Baseline:** $BaselineTag

## Summary

Platform release hardening: pinned container images, Olares distribution package, verification automation, US-V04 production engine attestation, and operational runbooks.

## Changes since $BaselineTag

``````
$log
``````

## Pinned images

| Service | Image |
|---------|-------|
| API | ``aimpos-api:$Version`` |
| Web | ``aimpos-web:$Version`` |
| Worker | ``aimpos-worker:$Version`` |

## Verification

``````powershell
make verify-all
make verify-all-olares
``````

## Upgrade

See ``docs/release/UPGRADE-GUIDE.md`` and ``docs/release/UPGRADE-CHECKLIST.md``.

"@

$outFile = Join-Path $OutDir "$Version.md"
Set-Content -Path $outFile -Value $body -Encoding UTF8
Write-Host "Wrote $outFile"
