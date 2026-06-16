# Ensure SSH tunnels to Olares shared Ollama + ComfyUI are up before the local worker starts.
# Called automatically by `make up-dev`.
param(
    [int]$MaxWaitSec = 45,
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" })
)

$ErrorActionPreference = "Stop"

function Test-AiEndpoint([string]$Url) {
    try {
        Invoke-WebRequest -Uri $Url -TimeoutSec 8 -UseBasicParsing | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-BothAiEndpoints {
    return (Test-AiEndpoint "http://127.0.0.1:11434/api/tags") -and
           (Test-AiEndpoint "http://127.0.0.1:8190/system_stats")
}

Write-Host "=== Olares shared AI tunnels ==="

if (Test-BothAiEndpoints) {
    Write-Host "Ollama (:11434) and ComfyUI (:8190) already reachable via localhost."
    exit 0
}

Write-Host "Starting tunnels to $OlaresHost ..."
& "$PSScriptRoot/start-olares-tunnels.ps1" -AiOnly

$deadline = (Get-Date).AddSeconds($MaxWaitSec)
while ((Get-Date) -lt $deadline) {
    if (Test-BothAiEndpoints) {
        Write-Host "Olares shared AI ready:"
        Write-Host "  Ollama  -> http://localhost:11434"
        Write-Host "  ComfyUI -> http://localhost:8190"
        exit 0
    }
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "ERROR: Olares shared AI is not reachable on localhost after ${MaxWaitSec}s." -ForegroundColor Red
Write-Host "  - Can you SSH to $OlaresHost ?"
Write-Host "  - Is the Olares ComfyUI pod running? (port-forward may need a restart on the host)"
Write-Host "  - Try manually: pwsh scripts/dev/start-olares-tunnels.ps1 -AiOnly"
exit 1
