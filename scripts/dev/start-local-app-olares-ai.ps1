# Local app stack (Postgres/MinIO/Redis/API/Worker/Temporal/Web) + Olares shared AI.
# Thin wrapper — daily dev is just:  make up-dev
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

Write-Host "=== AIMPOS local app + Olares shared AI (via make up-dev) ==="
& make up-dev
