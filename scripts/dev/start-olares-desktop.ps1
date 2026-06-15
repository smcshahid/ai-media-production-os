# Recommended desktop setup: local web only, full backend on Olares.
# Stops local Docker stack, opens API tunnel, starts Vite dev server.
param(
    [int]$ApiLocalPort = 18000,
    [int]$WebPort = 5173,
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

Write-Host "=== AIMPOS desktop → Olares (web-only) ==="

# 1. Stop local compose stack (frees :8000/:5173 and avoids hitting local API)
Write-Host "Stopping local Docker stack..."
docker compose -f deploy/compose/docker-compose.yml `
    -f deploy/compose/docker-compose.dev.yml `
    --env-file .env down 2>$null

# 2. SSH tunnel to Olares API
& "$PSScriptRoot/start-olares-tunnels.ps1" -ApiOnly -ApiLocalPort $ApiLocalPort

# 3. Fetch Olares API token for login hint
$OlaresHost = if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }
$token = (ssh -o BatchMode=yes $OlaresHost `
    "sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d" 2>$null).Trim()
if ($token) {
    Write-Host ""
    Write-Host "Sign in at http://localhost:${WebPort} with API token:"
    Write-Host "  $token"
    Write-Host ""
}

# 4. Start Vite dev server
$env:VITE_API_URL = "http://localhost:${ApiLocalPort}"
Write-Host "Starting web dev server (VITE_API_URL=$($env:VITE_API_URL))..."
Set-Location web
if (-not (Test-Path node_modules)) { npm install }
Write-Host "Open http://localhost:${WebPort}"
npm run dev
