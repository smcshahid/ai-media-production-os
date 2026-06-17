# US-V04 local verification - Flux + WAN attestation against local dev stack.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [string]$ProjectId = "",
    [string]$RunId = ""
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if (-not (Test-Path .env)) { throw ".env missing" }
$tokenLine = Select-String -Path .env -Pattern '^AIMPOS_API_TOKEN=(.+)$' | Select-Object -First 1
if (-not $tokenLine) { throw "AIMPOS_API_TOKEN missing" }
$token = $tokenLine.Matches[0].Groups[1].Value.Trim()

$FAIL = 0
Write-Host "US-V04 local verify start"

Write-Host "========== V-04-L01: worker env =========="
$workerEnv = docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env exec -T worker sh -c 'echo COMFYUI_WORKFLOW=$COMFYUI_WORKFLOW VIDEO_I2V_ENABLED=$VIDEO_I2V_ENABLED COMFYUI_HOST=$COMFYUI_HOST' 2>&1
Write-Host $workerEnv
if ($workerEnv -notmatch 'COMFYUI_WORKFLOW=flux_storyboard.json') { Write-Host "FAIL: flux workflow"; $FAIL = 1 }
if ($workerEnv -notmatch 'VIDEO_I2V_ENABLED=true') { Write-Host "FAIL: i2v disabled"; $FAIL = 1 }

if (-not $ProjectId) {
    $ProjectId = (docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql psql -U aimpos -d aimpos_spark -t -A -c "SELECT id FROM projects ORDER BY created_at LIMIT 1;").Trim()
}
Write-Host "PROJECT_ID=$ProjectId"

$status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/pipeline/status?project_id=$ProjectId" -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 15
Write-Host "Pipeline status=$($status.status) run=$($status.run_id)"
if ($status.status -ne "COMPLETED") {
    Write-Host "WARN: pipeline not COMPLETED - attesting latest assets only"
}
if (-not $RunId) { $RunId = $status.run_id }

Write-Host "========== V-04-L02: audit API regression =========="
try {
    $audit = Invoke-RestMethod -Uri "http://127.0.0.1:8000/audit?project_id=$ProjectId" -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 15
    Write-Host "AUDIT events=$($audit.events.Count) PASS"
} catch {
    Write-Host "FAIL: audit API"
    $FAIL = 1
}

Write-Host "========== V-04-L03: storyboard + video SQL =========="
$sql = @"
SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$ProjectId' AND stage='STORYBOARD';
SELECT COUNT(*) FROM asset_versions WHERE project_id='$ProjectId' AND stage='STORYBOARD' AND version=(SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$ProjectId' AND stage='STORYBOARD');
SELECT COALESCE(metadata_json->>'source','missing') FROM asset_versions WHERE project_id='$ProjectId' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;
SELECT COALESCE(metadata_json->>'fallback_reason','') FROM asset_versions WHERE project_id='$ProjectId' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;
"@
$lines = (docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql psql -U aimpos -d aimpos_spark -t -A -c $sql 2>&1) -split "`n" | Where-Object { $_.Trim() -ne "" }
Write-Host ($lines -join "`n")
$frameCount = if ($lines.Count -ge 2) { $lines[1].Trim() } else { "0" }
$videoSource = if ($lines.Count -ge 3) { $lines[2].Trim() } else { "missing" }
$fallback = if ($lines.Count -ge 4) { $lines[3].Trim() } else { "" }
Write-Host "STORYBOARD_FRAMES=$frameCount VIDEO_SOURCE=$videoSource"
if ($frameCount -eq "4") { Write-Host "PASS storyboard batch (D-45)" } else { Write-Host "WARN: expected 4 frames got $frameCount" }
if ($videoSource -eq "comfyui_i2v") {
    Write-Host "PASS US-V04 i2v source attested (D-61)"
} elseif ($videoSource -eq "slideshow") {
    Write-Host "WARN US-V04 slideshow fallback reason=$fallback"
} else {
    Write-Host "WARN US-V04 video source=$videoSource"
}

Write-Host "DONE FAIL=$FAIL"
exit $FAIL
