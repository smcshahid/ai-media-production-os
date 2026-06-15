# Local app stack (Postgres/MinIO/Redis/API/Worker/Temporal/Web) + Olares shared AI.
# Requires start-olares-tunnels.ps1 (without -ApiOnly) running in another terminal.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

Write-Host "=== AIMPOS local app + Olares shared AI ==="

# Ensure AI tunnels exist (Ollama + ComfyUI from Olares shared services)
& "$PSScriptRoot/start-olares-tunnels.ps1" -AiOnly

Write-Host "Starting local app stack (no local Ollama/ComfyUI)..."
docker compose -f deploy/compose/docker-compose.yml `
    -f deploy/compose/docker-compose.dev.yml `
    -f deploy/compose/docker-compose.olares-hybrid.yml `
    --env-file .env up -d --remove-orphans

Write-Host ""
Write-Host "Local API:  http://localhost:8000"
Write-Host "Local web:  http://localhost:5173"
Write-Host "Ollama:     Olares shared via localhost:11434 tunnel"
Write-Host "ComfyUI:    Olares shared via localhost:8190 tunnel"
Write-Host "Login token: see AIMPOS_API_TOKEN in .env"
