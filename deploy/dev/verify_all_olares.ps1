# Phase 8 consolidated Olares verification entrypoint.
param(
    [string]$OlaresHost = $(if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }),
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
    [switch]$SkipUsv09
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $RepoRoot "evidence/phase-8-verification/olares-$(Get-Date -Format 'yyyy-MM-dd')/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$FAIL = 0
Write-Host "verify-all Olares start -> $OlaresHost"

bash deploy/k8s/lib/sync_manifest_to_olares.sh $OlaresHost $RepoRoot

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
    "deploy/release/manifest.yaml",
    "scripts/release/load-manifest-env.sh",
    "deploy/k8s/phase3d-verify/check_drift.sh",
    "deploy/k8s/phase3d-verify/run_check_drift.sh"
) -RunScript "run_check_drift.sh"

if (-not $SkipUsv09) {
    if ($env:TOKEN -and $env:PGPW -and $env:PROJECT) {
        & "$RepoRoot/deploy/dev/verify_usv09_olares.ps1" -OlaresHost $OlaresHost
        if ($LASTEXITCODE -ne 0) { $FAIL += 1 }
    } else {
        Write-Host "WARN TOKEN/PGPW/PROJECT unset — US-V09 E2E skipped (drift-only)"
    }
}

Write-Host "verify-all-olares DONE FAIL=$FAIL"
Write-Host "Logs: $logDir"
exit $FAIL
