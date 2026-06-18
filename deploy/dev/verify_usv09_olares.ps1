# US-V09 Olares platform re-attestation orchestrator (Phase 8).
param(
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [switch]$DriftOnly
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$logDir = Join-Path $RepoRoot "evidence/us-v09-verification/olares-$(Get-Date -Format 'yyyy-MM-dd')/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$FAIL = 0
Write-Host "US-V09 Olares verify start -> $OlaresHost"

scp -q (Join-Path $RepoRoot "deploy/release/manifest.yaml") "${OlaresHost}:/tmp/aimpos-manifest.yaml"
scp -q (Join-Path $RepoRoot "scripts/release/load-manifest-env.sh") "${OlaresHost}:/tmp/load-manifest-env.sh"

$copyFiles = @(
    "deploy/release/manifest.yaml",
    "scripts/release/load-manifest-env.sh",
    "deploy/k8s/phase3d-verify/check_drift.sh",
    "deploy/k8s/phase3d-verify/run_check_drift.sh",
    "deploy/k8s/lib/verify_common.sh",
    "deploy/k8s/usv09-verify/verify_usv09_e2e.sh"
)
foreach ($f in $copyFiles) {
    $local = Join-Path $RepoRoot $f
    if (-not (Test-Path $local)) { throw "missing $f" }
    scp -q $local "${OlaresHost}:/tmp/$(Split-Path $local -Leaf)"
}

Write-Host "========== US-V09: drift (manifest-driven) =========="
$driftLog = Join-Path $logDir "drift.log"
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
ssh -o BatchMode=yes -o ConnectTimeout=30 $OlaresHost "chmod +x /tmp/run_check_drift.sh /tmp/check_drift.sh /tmp/load-manifest-env.sh && ACCEPTANCE_IMAGE_TAG=usv08b-phase75 bash /tmp/run_check_drift.sh" 2>&1 | Tee-Object -FilePath $driftLog
$driftExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($driftExit -ne 0) { Write-Host "FAIL drift"; $FAIL = 1 } else { Write-Host "PASS drift" }

if ($DriftOnly) {
    Write-Host "US-V09 Olares DONE FAIL=$FAIL (drift-only)"
    exit $FAIL
}

Write-Host "========== US-V09: platform E2E =========="
$e2eLog = Join-Path $logDir "e2e-olares.log"
$remote = @'
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv09-evidence
chmod +x /tmp/verify_usv09_e2e.sh
bash /tmp/verify_usv09_e2e.sh
'@
$ErrorActionPreference = "Continue"
ssh -o BatchMode=yes $OlaresHost $remote 2>&1 | Tee-Object -FilePath $e2eLog
$e2eExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($e2eExit -ne 0) { Write-Host "FAIL E2E"; $FAIL = 1 } else { Write-Host "PASS E2E" }

scp -q "${OlaresHost}:/tmp/usv09-evidence/*" (Join-Path $RepoRoot "evidence/us-v09-verification/olares-$(Get-Date -Format 'yyyy-MM-dd')") 2>$null

Write-Host "US-V09 Olares DONE FAIL=$FAIL"
Write-Host "Logs: $logDir"
exit $FAIL
