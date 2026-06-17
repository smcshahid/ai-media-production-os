# Phase 3D consolidated Olares verification entrypoint.
param(
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $RepoRoot "evidence/phase-3d-verification/olares-$(Get-Date -Format 'yyyy-MM-dd')/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$FAIL = 0
Write-Host "verify-all Olares start -> $OlaresHost"

function Run-Remote {
    param([string]$Name, [string[]]$CopyFiles, [string]$RunScript)
    Write-Host "========== verify-all-olares: $Name =========="
    foreach ($f in $CopyFiles) {
        $local = Join-Path $RepoRoot $f
        if (-not (Test-Path $local)) { throw "missing $f" }
        $remote = "/tmp/" + (Split-Path $local -Leaf)
        scp -q $local "${OlaresHost}:$remote"
    }
    $logFile = Join-Path $logDir "$Name.log"
    ssh -o BatchMode=yes -o ConnectTimeout=30 $OlaresHost "chmod +x /tmp/$RunScript && bash /tmp/$RunScript" 2>&1 | Tee-Object -FilePath $logFile
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL $Name"; return 1 }
    Write-Host "PASS $Name"
    return 0
}

$FAIL += Run-Remote -Name "drift" -CopyFiles @(
    "deploy/k8s/phase3d-verify/check_drift.sh",
    "deploy/k8s/phase3d-verify/run_check_drift.sh"
) -RunScript "run_check_drift.sh"

$FAIL += Run-Remote -Name "release" -CopyFiles @(
    "deploy/k8s/phase3d-verify/verify_release.sh",
    "deploy/k8s/phase3d-verify/run_verify_release.sh",
    "deploy/k8s/phase3d-verify/check_drift.sh"
) -RunScript "run_verify_release.sh"

$FAIL += Run-Remote -Name "phase3c" -CopyFiles @(
    "deploy/k8s/phase3c-verify/verify_phase3c.sh",
    "deploy/k8s/phase3c-verify/run_olares_phase3c.sh"
) -RunScript "run_olares_phase3c.sh"

Write-Host "verify-all-olares DONE FAIL=$FAIL"
Write-Host "Logs: $logDir"
exit $FAIL
