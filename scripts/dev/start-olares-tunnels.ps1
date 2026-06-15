# Desktop → Olares SSH tunnels.
# Mode api-only:  -ApiOnly   (full Olares backend — recommended for daily use)
# Mode ai-only:    -AiOnly    (local app stack; Ollama + ComfyUI from Olares shared)
# Default:         API + Ollama + ComfyUI
param(
    [switch]$ApiOnly,
    [switch]$AiOnly,
    [int]$ApiLocalPort = 18000,
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$ApiClusterIp = $(if ($env:OLARES_API_CLUSTER_IP) { $env:OLARES_API_CLUSTER_IP } else { "10.233.21.231" })
)

$ErrorActionPreference = "Stop"

if ($ApiOnly -and $AiOnly) {
    throw "Use only one of -ApiOnly or -AiOnly."
}

if ($AiOnly -or (-not $ApiOnly)) {
    & "$PSScriptRoot/start-olares-ai-forwards.ps1"
}

$forwardArgs = @("-N")
if (-not $AiOnly) {
    Get-NetTCPConnection -LocalPort $ApiLocalPort -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    $forwardArgs += @("-L", "${ApiLocalPort}:${ApiClusterIp}:8000")
}
if (-not $ApiOnly) {
    foreach ($p in 11434, 8190) {
        Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
    $forwardArgs += @("-L", "11434:127.0.0.1:11434", "-L", "8190:127.0.0.1:8190")
}

Write-Host "Starting SSH tunnel to $OlaresHost ..."
if (-not $AiOnly) { Write-Host "  API  → http://localhost:${ApiLocalPort}" }
if (-not $ApiOnly) {
    Write-Host "  Ollama → http://localhost:11434"
    Write-Host "  ComfyUI → http://localhost:8190"
}

Start-Process -FilePath "ssh" -ArgumentList ($forwardArgs + $OlaresHost) -WindowStyle Hidden
Start-Sleep -Seconds 2

if (-not $AiOnly) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:${ApiLocalPort}/health" -TimeoutSec 8
        Write-Host "API health: $($health.status)"
    } catch {
        Write-Warning "API not yet reachable on :${ApiLocalPort} - wait a few seconds and retry."
    }
}
