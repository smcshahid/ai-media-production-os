# Phase 3D local verification — manifest pins, version compatibility, regressions.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$FAIL = 0
$manifest = Join-Path $RepoRoot "deploy/release/manifest.yaml"
Write-Host "Phase 3D local verify start"

if (-not (Test-Path $manifest)) {
    Write-Host "FAIL manifest missing"
    exit 1
}

$content = Get-Content $manifest -Raw

Write-Host "========== P3D-01: manifest present =========="
if ($content -match 'version:\s*"v0\.13\.0-phase3d"') {
    Write-Host "PASS release version"
} else {
    Write-Host "FAIL release version"
    $FAIL = 1
}

Write-Host "========== P3D-02: image pin completeness =========="
foreach ($img in @("aimpos-api", "aimpos-web", "aimpos-worker")) {
    if ($content -match $img) { Write-Host "PASS $img defined" }
    else { Write-Host "FAIL $img missing"; $FAIL = 1 }
}

Write-Host "========== P3D-03: alembic head contract =========="
if ($content -match 'alembic_head:\s*"(\d+)"') {
    $head = $Matches[1]
    Write-Host "MANIFEST_ALEMBIC=$head"
    if ($head -ne "0003") { Write-Host "FAIL alembic head"; $FAIL = 1 }
} else {
    Write-Host "FAIL alembic head missing"
    $FAIL = 1
}

if (Test-Path .env) {
    $pgUp = $false
    $workerUp = $false
    try {
        $pgUp = docker compose -f deploy/compose/docker-compose.yml --env-file .env ps postgresql 2>$null | Select-String "Up"
    } catch {
        Write-Host "SKIP docker unavailable for live checks"
    }
    if ($pgUp) {
        Write-Host "========== P3D-04: live alembic =========="
        $ver = (docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql `
            sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT version_num FROM alembic_version;"').Trim()
        Write-Host "LIVE_ALEMBIC=$ver"
        if ($ver -ne "0003") { Write-Host "FAIL live alembic mismatch"; $FAIL = 1 }
        else { Write-Host "PASS alembic match" }
    } else {
        Write-Host "SKIP postgres not running"
    }

    try {
        $workerUp = docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env ps worker 2>$null | Select-String "Up"
    } catch {
        $workerUp = $false
    }
    if ($workerUp) {
        Write-Host "========== P3D-05: worker env contract =========="
        $envOut = docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env exec -T worker `
            sh -c 'echo COMFYUI_WORKFLOW=$COMFYUI_WORKFLOW VIDEO_I2V_ENABLED=$VIDEO_I2V_ENABLED' 2>&1
        Write-Host $envOut
        if ($envOut -notmatch 'COMFYUI_WORKFLOW=flux_storyboard.json') { Write-Host "FAIL workflow"; $FAIL = 1 }
        if ($envOut -notmatch 'VIDEO_I2V_ENABLED=true') { Write-Host "FAIL i2v"; $FAIL = 1 }
    } else {
        Write-Host "SKIP worker not running"
    }
}

Write-Host "========== P3D-06: phase3c regression =========="
$dockerOk = $false
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
} catch { $dockerOk = $false }
if ($dockerOk) {
    & "$RepoRoot/deploy/dev/verify_phase3c_local.ps1"
    if ($LASTEXITCODE -ne 0) { $FAIL = 1 }
} else {
    Write-Host "SKIP phase3c regression (docker unavailable)"
}

Write-Host "DONE FAIL=$FAIL"
exit $FAIL
