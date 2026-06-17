# Phase 3D consolidated local verification entrypoint (D-72).
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [switch]$SkipBootstrap,
    [switch]$SkipUsv04,
    [switch]$SkipPhase3d
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$FAIL = 0
$logDir = Join-Path $RepoRoot "evidence/phase-3d-verification/local-$(Get-Date -Format 'yyyy-MM-dd')/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Run-Step {
    param([string]$Name, [scriptblock]$Block)
    Write-Host ""
    Write-Host "========== verify-all: $Name =========="
    $logFile = Join-Path $logDir "$Name.log"
    try {
        & $Block 2>&1 | Tee-Object -FilePath $logFile
        if ($LASTEXITCODE -ne 0) {
            Write-Host "FAIL $Name exit=$LASTEXITCODE"
            return 1
        }
        Write-Host "PASS $Name"
        return 0
    } catch {
        Write-Host "FAIL $Name $($_.Exception.Message)"
        return 1
    }
}

Write-Host "verify-all local start $(Get-Date -Format o)"

if (-not $SkipBootstrap) {
    $FAIL += Run-Step "bootstrap" { bash deploy/dev/verify_bootstrap.sh }
}

if (-not $SkipUsv04) {
    $FAIL += Run-Step "usv04" { & "$RepoRoot/deploy/dev/verify_usv04_local.ps1" }
}

$FAIL += Run-Step "phase3b" { & "$RepoRoot/deploy/dev/verify_phase3b_local.ps1" }
$FAIL += Run-Step "phase3c" { & "$RepoRoot/deploy/dev/verify_phase3c_local.ps1" }

if (-not $SkipPhase3d) {
    $FAIL += Run-Step "phase3d" { & "$RepoRoot/deploy/dev/verify_phase3d_local.ps1" }
}

Write-Host ""
Write-Host "verify-all DONE FAIL=$FAIL"
Write-Host "Logs: $logDir"
exit $FAIL
