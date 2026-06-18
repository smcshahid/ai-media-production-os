# Phase 8 consolidated local verification entrypoint (D-72 / TD-P75-02).
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [switch]$SkipBootstrap,
    [switch]$SkipUsv04,
    [switch]$SkipPhase3d,
    [switch]$SkipPhase4,
    [switch]$SkipPhase5,
    [switch]$SkipPhase6,
    [switch]$SkipPhase7,
    [switch]$SkipPhase75,
    [switch]$SkipManifest
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
        $output = & $Block 2>&1
        $exit = $LASTEXITCODE
        $output | Tee-Object -FilePath $logFile | Out-Null
        if ($exit -ne 0) {
            Write-Host "FAIL $Name exit=$exit"
            return 1
        }
        Write-Host "PASS $Name"
        return 0
    } catch {
        Write-Host "FAIL $Name $($_.Exception.Message)"
        return 1
    }
}

function Test-LiveApi {
    if (-not (Test-Path (Join-Path $RepoRoot ".env"))) { return $false }
    $tokenLine = Select-String -Path (Join-Path $RepoRoot ".env") -Pattern '^AIMPOS_API_TOKEN=(.+)$' | Select-Object -First 1
    if ($null -eq $tokenLine) { return $false }
    $token = $tokenLine.Matches[0].Groups[1].Value.Trim()
    $portLine = Select-String -Path (Join-Path $RepoRoot ".env") -Pattern '^API_PORT=(.+)$' | Select-Object -First 1
    $port = if ($portLine) { $portLine.Matches[0].Groups[1].Value.Trim() } else { "8000" }
    $statusCode = (curl.exe -s -o NUL -w "%{http_code}" -H "Authorization: Bearer $token" "http://127.0.0.1:$port/health" 2>$null)
    return $statusCode -eq "200"
}

Write-Host "verify-all local start $(Get-Date -Format o)"
$liveApi = Test-LiveApi
if (-not $liveApi) {
    Write-Host "WARN Live API unavailable - skipping usv04/phase3b/phase3c/phase3d integration gates"
}

if (-not $SkipManifest) {
    $FAIL += Run-Step "manifest" { python "$RepoRoot/scripts/release/validate-manifest.py" }
}

if (-not $SkipBootstrap) {
    $FAIL += Run-Step "bootstrap" { & "$RepoRoot/scripts/dev/ensure-db-migrated.ps1" }
}

if (-not $SkipUsv04 -and $liveApi) {
    $FAIL += Run-Step "usv04" { & "$RepoRoot/deploy/dev/verify_usv04_local.ps1" }
}

if ($liveApi) {
    $FAIL += Run-Step "phase3b" { & "$RepoRoot/deploy/dev/verify_phase3b_local.ps1" }
    $FAIL += Run-Step "phase3c" { & "$RepoRoot/deploy/dev/verify_phase3c_local.ps1" }
} else {
    Write-Host "SKIP phase3b/phase3c (no live API)"
}

if (-not $SkipPhase3d -and $liveApi) {
    $FAIL += Run-Step "phase3d" { & "$RepoRoot/deploy/dev/verify_phase3d_local.ps1" }
} elseif (-not $SkipPhase3d) {
    Write-Host "SKIP phase3d (no live API)"
}

if (-not $SkipPhase4) {
    $FAIL += Run-Step "phase4" { & "$RepoRoot/deploy/dev/verify_phase4_local.ps1" }
}

if (-not $SkipPhase5) {
    $FAIL += Run-Step "phase5" { & "$RepoRoot/deploy/dev/verify_phase5_local.ps1" }
}

if (-not $SkipPhase6) {
    $FAIL += Run-Step "phase6" { & "$RepoRoot/deploy/dev/verify_phase6_local.ps1" }
}

if (-not $SkipPhase7) {
    $FAIL += Run-Step "phase7" { & "$RepoRoot/deploy/dev/verify_phase7_local.ps1" }
}

if (-not $SkipPhase75) {
    $FAIL += Run-Step "phase75" { & "$RepoRoot/deploy/dev/verify_usv08b_local.ps1" }
}

Write-Host ""
Write-Host "verify-all DONE FAIL=$FAIL"
Write-Host "Logs: $logDir"
exit $FAIL
